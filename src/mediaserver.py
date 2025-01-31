import atexit
import base64
import json
import os
import sys
from signal import SIGINT, SIGTERM, signal

from authlib.integrations.flask_oauth2 import ResourceProtector, current_token
from authlib.oauth2 import OAuth2Error
from flask import Flask, Response, jsonify, redirect, request
from flask import json

from os_authlib.token_validator import create_openslides_token_validator
from .auth.auth import AUTHENTICATION_HEADER, check_file_id
from .config_handling import init_config, is_dev_mode
from .database import Database
from .exceptions import BadRequestError, HttpError, NotFoundError
from .logging import init_logging

app = Flask(__name__)
with app.app_context():
    init_logging()
    init_config()
    database = Database()

app.config['DEBUG'] = True
app.debug = True

require_oauth = ResourceProtector()
require_oauth.register_token_validator(create_openslides_token_validator())

@app.errorhandler(Exception)
def handle_view_error(error):
    raise error
    # if isinstance(error, HttpError):
    #     app.logger.error(
    #         f"Request to {request.path} resulted in {error.status_code}: "
    #         f"{error.message}"
    #     )
    #     res_content = {"message": f"Media-Server: {error.message}"}
    #     response = jsonify(res_content)
    #     response.status_code = error.status_code
    #     return response
    # elif isinstance(error, OAuth2Error):
    #     app.logger.error(
    #         f"Request to {request.path} resulted in {error.status_code}: "
    #         f"{error.description} (AuthlibHTTPError)"
    #     )
    #     res_content = {"message": f"Media-Server: {error.description}"}
    #     response = jsonify(res_content)
    #     response.status_code = error.status_code
    #     return response
    # else:
    #     app.logger.error(f"Request to {request.path} resulted in {error} ({type(error)})")
    #     res_content = {"message": "Media-Server: Internal Server Error"}
    #     response = jsonify(res_content)
    #     response.status_code = 500
    #     return response


@app.route("/system/media/get/<int:file_id>")
@require_oauth()
def serve(file_id):
    # get file id
    autoupdate_headers = dict(request.headers)
    del_keys = [key for key in autoupdate_headers if "content" in key]
    for key in del_keys:
        del autoupdate_headers[key]
    ok, filename, auth_header = check_file_id(file_id, autoupdate_headers, current_token.os_uid)
    if not ok:
        raise NotFoundError()

    app.logger.debug(f'Filename for "{file_id}" is {filename}')

    # Query file from db
    global database
    data, mimetype = database.get_file(file_id)

    # Send data (chunked)
    def chunked(size, source):
        for i in range(0, len(source), size):
            yield bytes(source[i : i + size])

    block_size = app.config["MEDIA_BLOCK_SIZE"]
    response = Response(chunked(block_size, data), mimetype=mimetype)
    # http headers can only be encoded using latin1
    filename_latin1 = filename.encode("latin1", errors="replace").decode("latin1")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{filename_latin1}"'
    )

    client_cache_duration = int(app.config["MEDIA_CLIENT_CACHE_DURATION"] or 0)
    if client_cache_duration > 0 and not is_dev_mode():
        response.headers["Cache-Control"] = f"private, max-age={client_cache_duration}"

    if auth_header:
        response.headers[AUTHENTICATION_HEADER] = auth_header
    return response


@app.route("/internal/media/upload_mediafile/", methods=["POST"])
@require_oauth()
def media_post():
    dejson = get_json_from_request()
    try:
        file_data = base64.b64decode(dejson["file"].encode())
    except Exception:
        raise BadRequestError("cannot decode base64 file")
    try:
        file_id = int(dejson["id"])
        mimetype = dejson["mimetype"]
    except Exception:
        raise BadRequestError(
            f"The post request.data is not in right format: {request.data}"
        )
    app.logger.debug(f"to database {file_id} {mimetype}")
    global database
    database.set_mediafile(file_id, file_data, mimetype)
    return "", 200


@app.route("/internal/media/duplicate_mediafile/", methods=["POST"])
@require_oauth()
def duplicate_mediafile():
    source_id, target_id = get_ids(get_json_from_request())
    app.logger.debug(f"source_id {source_id} and target_id {target_id}")
    global database
    # Query file source_id from db
    data, mimetype = database.get_file(source_id)
    # Insert mediafile in target_id into db
    database.set_mediafile(target_id, data, mimetype)
    return "", 200


def get_json_from_request():
    try:
        decoded = request.data.decode()
        dejson = json.loads(decoded)
        return dejson
    except Exception:
        raise BadRequestError("request.data is not json")


def get_ids(dejson):
    try:
        source_id = int(dejson["source_id"])
        target_id = int(dejson["target_id"])
    except Exception:
        raise BadRequestError(
            f"The post request.data is not in right format: {request.data}"
        )
    return source_id, target_id


def shutdown(database):
    app.logger.info("Stopping the server...")
    database.shutdown()
    app.logger.info("Done!")


atexit.register(shutdown, database)

for sig in (SIGTERM, SIGINT):
    signal(sig, lambda *_: sys.exit(0))

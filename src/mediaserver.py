import atexit
import base64
import json

from flask import Flask, Response, request

from .auth import get_mediafile_id
from .config_handling import init_config
from .database import Database
from .exceptions import BadRequestError, HttpError, NotFoundError
from .logging import init_logging

app = Flask(__name__)
init_logging(app)
init_config(app)
database = Database(app)

app.logger.info("Started Media-Server")


@app.errorhandler(HttpError)
def handle_view_error(error):
    app.logger.error(
        f"Request to {request.path} resulted in {error.status_code}: "
        f"{error.message}"
    )
    return f"Media-Server: {error.message}", error.status_code


@app.route("/system/media/get/<int:meeting_id>/<path:path>")
def serve(meeting_id, path):
    if not path:
        raise NotFoundError()

    # get mediafile id
    cookie = request.headers.get("Cookie", "")
    media_id = get_mediafile_id(meeting_id, path, app, cookie)
    app.logger.debug(f'Id for "{path}" and "{meeting_id}" is {media_id}')

    # Query file from db
    global database
    data, mimetype = database.get_mediafile(media_id)

    # Send data (chunked)
    def chunked(size, source):
        for i in range(0, len(source), size):
            yield bytes(source[i : i + size])

    block_size = app.config["BLOCK_SIZE"]
    return Response(chunked(block_size, data), mimetype=mimetype)


@app.route("/internal/media/upload/", methods=["POST"])
def media_post():
    try:
        decoded = request.data.decode()
        dejson = json.loads(decoded)
    except Exception:
        raise BadRequestError("request.data is not json")
    try:
        media = base64.b64decode(dejson["file"].encode())
    except Exception:
        raise BadRequestError("cannot decode base64 file")
    try:
        media_id = int(dejson["id"])
        mimetype = dejson["mimetype"]
    except Exception:
        raise BadRequestError(
            f"The post request.data is not in right format: {request.data}"
        )
    app.logger.debug(f"to database media {media_id} {mimetype}")
    global database
    database.set_mediafile(media_id, media, mimetype)
    return f"Mediaserver: add {media_id} to db", 200


# for testing
@app.route("/system/presenter", methods=["POST"])
def dummy_presenter():
    app.logger.debug(f"dummy_presenter gets: {request.json}")
    meeting_id = request.json[0]["data"]["meeting_id"]
    return f"[{meeting_id}]"


def shutdown(database):
    app.logger.info("Stopping the server...")
    database.shutdown()
    app.logger.info("Done!")


atexit.register(shutdown, database)

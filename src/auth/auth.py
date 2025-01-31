import requests
from flask import current_app as app
from flask import request

from os_authlib import (
    AUTHENTICATION_HEADER,
    AuthenticateException,
    AuthHandler,
    InvalidCredentialsException, AUTHORIZATION_HEADER, )
from ..exceptions import ServerError


def get_user_id():
    """Returns the user id from the auth cookie."""
    auth_handler = AuthHandler(app.logger.debug)
    authentication = request.headers.get(AUTHORIZATION_HEADER, "")
    app.logger.info(f"Get user id from auth header: {authentication}")
    try:
        (user_id, _) = auth_handler.authenticate(authentication)
    except (AuthenticateException, InvalidCredentialsException):
        return -1
    return user_id


def check_login():
    """Returns whether the user is logged in or not."""
    user_id = get_user_id()
    if user_id == -1:
        return False
    return True


def check_file_id(file_id, autoupdate_headers, user_id):
    """
    Returns a triple: ok, filename, auth_header.
    filename is given, if ok=True. If ok=false, the user has no perms.
    if auth_header is returned, it must be set in the response.
    """
    if user_id == -1:
        raise ServerError("Could not find authentication")

    autoupdate_url = get_autoupdate_url(user_id)
    payload = [
        {
            "collection": "mediafile",
            "fields": {"id": None, "filename": None},
            "ids": [file_id],
        }
    ]
    app.logger.debug(f"Send check request: {autoupdate_url}: {payload}")

    try:
        response = requests.post(
            autoupdate_url, headers=autoupdate_headers, json=payload
        )
    except requests.exceptions.ConnectionError as e:
        app.logger.error(str(e))
        raise ServerError("The server didn't respond")

    if response.status_code != requests.codes.ok:
        raise ServerError(
            "The server responded with an unexpected code "
            f"{response.status_code}: {response.content}"
        )

    # Expects: {ok: bool, filename: Optional[str]}

    try:
        content = response.json()
    except ValueError:
        raise ServerError("The Response does not contain valid JSON.")
    if not isinstance(content, dict):
        raise ServerError("The returned content is not a dict.")

    auth_header = response.headers.get(AUTHORIZATION_HEADER)

    if (
            f"mediafile/{file_id}/id" not in content
            or content[f"mediafile/{file_id}/id"] != file_id
    ):
        return False, None, auth_header

    if f"mediafile/{file_id}/filename" not in content:
        raise ServerError("The autoupdate did not provide a filename")

    return True, content[f"mediafile/{file_id}/filename"], auth_header


def get_autoupdate_url(user_id):
    autoupdate_host = app.config["AUTOUPDATE_HOST"]
    autoupdate_port = app.config["AUTOUPDATE_PORT"]
    return f"http://{autoupdate_host}:{autoupdate_port}/internal/autoupdate?user_id={user_id}&single=1"

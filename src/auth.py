from urllib import parse

import requests
from flask import current_app as app
from flask import request
from osauthlib import (
    AUTHENTICATION_HEADER,
    COOKIE_NAME,
    AuthenticateException,
    AuthHandler,
    InvalidCredentialsException,
)

from .exceptions import ServerError


def check_login_valid():
    """Returns whether the user is logged in or not."""
    auth_handler = AuthHandler(app.logger.debug)
    cookie = request.cookies.get(COOKIE_NAME, "")
    try:
        auth_handler.authenticate_only_refresh_id(parse.unquote(cookie))
    except (AuthenticateException, InvalidCredentialsException):
        return False
    return True


def check_file_id(file_id, autoupdate_headers):
    """
    Returns a triple: ok, filename, auth_header.
    filename is given, if ok=True. If ok=false, the user has no perms.
    if auth_header is returned, it must be set in the response.
    """
    auth_handler = AuthHandler(app.logger.debug)
    cookie = request.cookies.get(COOKIE_NAME, "")
    try:
        user_id = auth_handler.authenticate_only_refresh_id(parse.unquote(cookie))
    except (AuthenticateException, InvalidCredentialsException):
        raise ServerError("Could not parse auth cookie")

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

    auth_header = response.headers.get(AUTHENTICATION_HEADER)

    if content.get(f"mediafile/{file_id}/id") != file_id:
        return False, None, auth_header

    if f"mediafile/{file_id}/filename" not in content:
        raise ServerError("The autoupdate did not provide a filename")

    return True, content[f"mediafile/{file_id}/filename"], auth_header


def check_meeting_mediafile_id(meeting_mediafile_id, autoupdate_headers):
    """
    Resolves a meeting_mediafile_id to a global file_id and filename.
    Returns a quadruple: ok, file_id, filename, auth_header.
    If ok=False, the user has no perms or the object doesn't exist.
    If auth_header is returned, it must be set in the response.
    """
    auth_handler = AuthHandler(app.logger.debug)
    cookie = request.cookies.get(COOKIE_NAME, "")
    try:
        user_id = auth_handler.authenticate_only_refresh_id(parse.unquote(cookie))
    except (AuthenticateException, InvalidCredentialsException):
        raise ServerError("Could not parse auth cookie")

    autoupdate_url = get_autoupdate_url(user_id)
    payload = [
        {
            "collection": "meeting_mediafile",
            "fields": {
                "id": None,
                "mediafile_id": {
                    "type": "relation",
                    "collection": "mediafile",
                    "fields": {
                        "id": None,
                        "filename": None,
                    },
                },
            },
            "ids": [meeting_mediafile_id],
        },
    ]
    app.logger.debug(
        f"Send meeting mediafile check request: {autoupdate_url}: {payload}"
    )

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

    try:
        content = response.json()
    except ValueError:
        raise ServerError("The Response does not contain valid JSON.")
    if not isinstance(content, dict):
        raise ServerError("The returned content is not a dict.")

    auth_header = response.headers.get(AUTHENTICATION_HEADER)
    mmf_prefix = f"meeting_mediafile/{meeting_mediafile_id}"

    if content.get(f"{mmf_prefix}/id") != meeting_mediafile_id:
        return False, None, None, auth_header

    if not (mediafile_id := content.get(f"{mmf_prefix}/mediafile_id")):
        raise ServerError("The autoupdate did not provide a mediafile_id")

    if not (filename := content.get(f"mediafile/{mediafile_id}/filename")):
        raise ServerError("The autoupdate did not provide a filename")

    return (
        True,
        mediafile_id,
        filename,
        auth_header,
    )


def get_autoupdate_url(user_id):
    autoupdate_host = app.config["AUTOUPDATE_HOST"]
    autoupdate_port = app.config["AUTOUPDATE_PORT"]
    return f"http://{autoupdate_host}:{autoupdate_port}/internal/autoupdate?user_id={user_id}&single=1"

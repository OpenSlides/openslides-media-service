import os

import requests
from flask import current_app as app
from flask import request
from osauthlib import AUTHENTICATION_HEADER  # noqa: F401 (re-exported)
from osauthlib import (
    AUTHORIZATION_HEADER,
    COOKIE_NAME,
    AuthenticateException,
    AuthHandler,
    InvalidCredentialsException,
    OidcAuthenticator,
)

from ..exceptions import ServerError

# Lazy-initialized OIDC authenticator
_oidc_authenticator = None


def _get_oidc_authenticator():
    global _oidc_authenticator
    if _oidc_authenticator is None:
        issuer = os.environ.get("OPENID_CONNECT_ISSUER", "")
        client_id = os.environ.get("OPENID_CONNECT_CLIENT_ID", "")
        if issuer and client_id:
            _oidc_authenticator = OidcAuthenticator(
                issuer=issuer,
                audience=client_id,
                debug_fn=app.logger.debug,
            )
    return _oidc_authenticator


def get_user_id_from_oidc():
    """
    Authenticate via OIDC token or fall back to legacy auth.
    Returns user_id or -1 on failure.
    """
    authorization = request.headers.get(AUTHORIZATION_HEADER, "")
    if not authorization:
        return -1

    token = authorization
    if token.lower().startswith("bearer "):
        token = token[7:]

    # Try OIDC if authenticator is configured
    oidc = _get_oidc_authenticator()
    if oidc and oidc.is_oidc_token(token):
        try:
            keycloak_id = oidc.extract_keycloak_id(token)
            app.logger.debug(f"OIDC token validated, keycloak_id: {keycloak_id}")
            # Look up user by keycloak_id via database
            user_id = _lookup_user_by_keycloak_id(keycloak_id)
            return user_id
        except (AuthenticateException, InvalidCredentialsException) as e:
            app.logger.warning(f"OIDC authentication failed: {e}")
            return -1

    # Fall back to legacy auth
    return get_user_id()


def _lookup_user_by_keycloak_id(keycloak_id):
    """Look up OpenSlides user ID by keycloak_id via the database."""
    import psycopg2

    try:
        password = app.config.get("MEDIA_DATABASE_PASSWORD", "openslides")
        conn = psycopg2.connect(
            host=app.config["MEDIA_DATABASE_HOST"],
            port=app.config["MEDIA_DATABASE_PORT"],
            dbname=app.config["MEDIA_DATABASE_NAME"],
            user=app.config["MEDIA_DATABASE_USER"],
            password=password,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM user_t WHERE keycloak_id = %s AND is_active = true",
                    (keycloak_id,),
                )
                row = cur.fetchone()
                if row:
                    return row[0]
                app.logger.warning(
                    f"No active user found with keycloak_id: {keycloak_id}"
                )
                return -1
        finally:
            conn.close()
    except Exception as e:
        app.logger.error(f"Database lookup for keycloak_id failed: {e}")
        return -1


def get_user_id():
    """Returns the user id from the auth cookie."""
    auth_handler = AuthHandler(app.logger.debug)
    authentication = request.headers.get(AUTHORIZATION_HEADER, "")
    refresh_id = request.cookies.get(COOKIE_NAME, "")
    app.logger.info(f"Get user id from auth header: {authentication}")
    try:
        user_id, _ = auth_handler.authenticate(authentication, refresh_id)
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

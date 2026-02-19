from collections.abc import Mapping
from os.path import join

import jwt
import psycopg2
import pytest
import requests
from os_authlib import COOKIE_NAME
from os_authlib.config import AUTH_DEV_COOKIE_SECRET

GET_URL = "http://media:9006/system/media/get/"


@pytest.fixture(autouse=True)
def reset_db():
    """Deletes all mediafiles except for id=2 and id=3 (example data)"""
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM media.mediafile_data WHERE id NOT IN (2, 3)")


def get_connection():
    return psycopg2.connect(
        host="postgres",
        port=5432,
        database="openslides",
        user="openslides",
        password="openslides",
    )


def get_mediafile(id, use_cookie=True):
    cookies = {}
    if use_cookie:
        # dummy cookie for testing
        token = jwt.encode({"userId": 1}, AUTH_DEV_COOKIE_SECRET)
        authentication = f"bearer {token}"
    return requests.get(join(GET_URL, str(id)), headers={'Authentication': authentication}, allow_redirects=False)

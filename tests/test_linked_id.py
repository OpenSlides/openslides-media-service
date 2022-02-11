import base64

import requests

from tests.base import query_db, reset_db
from tests.test_get import GET_URL
from tests.test_upload_mediafile import UPLOAD_URL


def test_good():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 31,
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 200
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 32,
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 200
    row = query_db(32)
    assert row[0] == 32
    assert row[4] == 31

    resp = requests.get(GET_URL + "32")
    assert resp.status_code == 200
    assert resp.content == b"testtesttest"

    resp = requests.get(GET_URL + "31")
    assert resp.status_code == 200
    assert resp.content == b"testtesttest"

    reset_db()

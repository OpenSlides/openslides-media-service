# Tests for the openslides media service
import base64

import pytest
import requests

from .base import get_connection

UPLOAD_URL = "http://media:9006/internal/media/upload_resource/"
GET_URL = "http://media:9006/system/media/get_resource/"


@pytest.fixture(autouse=True)
def reset_db():
    """Deletes all mediafiles except for id=2 and id=3 (example data)"""
    conn = get_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM resource_data WHERE id NOT IN (2, 3)")


def test_good():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 4,
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 200
    assert resp.text == ""

    get_response = requests.get(GET_URL + "4")
    assert get_response.status_code == 200
    assert get_response.content == b"testtesttest"
    assert "text/plain" in get_response.headers.get("Content-Type")


def test_twice():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 4,
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 200

    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 500


def test_not_base64_file():
    payload = {
        "file": "XXX",
        "id": 4,
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 400
    assert "message" in resp.json()


def test_broken_id():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": "XXX",
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 400
    assert "message" in resp.json()


def test_missing_mimetype():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 6,
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 400
    assert "message" in resp.json()


def test_missing_id():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "mimetype": "text/plain",
    }
    resp = requests.post(UPLOAD_URL, json=payload)
    assert resp.status_code == 400
    assert "message" in resp.json()

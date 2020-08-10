# Tests for the openslides media service
import base64

import requests

GET_URL = "http://media:9006/system/media/get/"
POST_URL = "http://media:9006/internal/media/upload/"


def test_mediaservice_positiv():
    # wait the service to start
    req = requests.get(GET_URL + "2/test")
    assert req.status_code == 200
    assert req.content == b"a2"
    assert "text/plain" in req.headers.get("Content-Type")


def test_mediaservice_not_found():
    req = requests.get(GET_URL + "4/test")
    assert req.status_code == 500


def test_mediaservice_auth_problem():
    req = requests.get(GET_URL + "12/test")
    assert req.status_code == 500


def test_mediaservice_post_good_test():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 5,
        "mimetype": "text/plain",
    }
    req = requests.post(POST_URL, json=payload)
    assert req.status_code == 200

    req2 = requests.get(GET_URL + "5/test")
    assert req2.status_code == 200
    assert req2.content == b"testtesttest"
    assert "text/plain" in req2.headers.get("Content-Type")


def test_mediaservice_post_not_base64_file():
    payload = {
        "file": "XXX",
        "id": 7,
        "mimetype": "text/plain",
    }
    req = requests.post(POST_URL, json=payload)
    assert req.status_code == 500


def test_mediaservice_post_broken_id():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": "XXX",
        "mimetype": "text/plain",
    }
    req = requests.post(POST_URL, json=payload)
    assert req.status_code == 500


def test_mediaservice_missing_mimetype():
    payload = {
        "file": base64.b64encode(b"testtesttest").decode(),
        "id": 6,
    }
    req = requests.post(POST_URL, json=payload)
    assert req.status_code == 500

import pytest
import requests

from tests.base import reset_db

DUPLICATE_URL = "http://media:9006/internal/media/duplicate_mediafile/"
GET_URL = "http://media:9006/system/media/get/"


@pytest.fixture(autouse=True)
def reset_db_in_duplicate_mediafile():
    reset_db()


def test_good():
    payload = {
        "source_id": 2,
        "target_id": 5,
    }
    response = requests.post(DUPLICATE_URL, json=payload)
    assert response.status_code == 200
    assert response.text == ""

    get_response = requests.get(GET_URL + "5")
    assert get_response.status_code == 200
    assert get_response.content == b"a2"
    assert "text/plain" in get_response.headers.get("Content-Type")


def test_broken_source():
    payload = {
        "source_id": 4,
        "target_id": 5,
    }
    response = requests.post(DUPLICATE_URL, json=payload)
    assert response.status_code == 500
    assert "message" in response.json()


def test_broken_target():
    payload = {
        "source_id": 2,
        "target_id": 3,
    }
    response = requests.post(DUPLICATE_URL, json=payload)
    assert response.status_code == 500
    assert "message" in response.json()


def test_empty():
    payload = {}
    response = requests.post(DUPLICATE_URL, json=payload)
    assert response.status_code == 400
    assert "message" in response.json()

import pytest
import json

from typing import List, Callable, Optional, Union

import flask as fl

from app import create_app, Route
from config import HASH_LENGTH
from tests.environment import (generate_random_url, get_invalid_hashes,
                               get_test_bytes_object, get_uncloseable_bytes,
                               remove_test_file, test_file_name)


@pytest.fixture(scope='module')
def client():
    flask_app = create_app()
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()


def assert_equals(response: fl.wrappers.Response, status_code: int) -> dict:
    """Base function that check response status
    Equals to passed status_code and response has a message field

    Args:
        response (): .
        status_code (int): .

    Return:
        response dictionary

    Raises:
        AssertionError: If status_code doesn't match or response has no
        message field

    """

    json_response = response.get_json()

    assert response.status_code == status_code
    assert "message" in json_response.keys()
    assert "status_code" in json_response.keys()
    assert json_response["status_code"] == status_code

    return json_response


def test_root_get(client):
    response = client.get('/')
    assert_equals(response, status_code=200)


def use_not_allowed_methods(client, url: str, not_allowed_methods: Union[Callable, List[Callable]], json_response_code: Optional[int] = None):
    """Checks if server allow method passed in not_allowed_methods

    Args:
        client (type): flask.testing.FlaskClient
        url (str): target URL
        not_allowed_methods (Union[Callable, List[Callable]]): list of methods or a single one
        json_response_code (Optional[int]): Specified response code that should be received

    Raises:
        AssertionError: If any of passed methods will fail assert_equals

    """

    json_response_code = json_response_code or 405
    data = json.dumps({"some": "data"})

    if not isinstance(not_allowed_methods, (list, tuple, set)):
        not_allowed_methods = [not_allowed_methods]

    for method in not_allowed_methods:
        response = method(url, data=data, content_type='application/json')
        assert_equals(response, json_response_code)


def test_root_post(client):
    use_not_allowed_methods(client, '/', [client.post, client.put, client.delete, client.patch])


def test_upload_invalid(client):
    use_not_allowed_methods(client, Route.upload, [client.get, client.delete, client.patch])


def test_download_invalid(client):
    use_not_allowed_methods(client, Route.download, [client.post, client.put, client.delete, client.patch])


def test_delete_invalid(client):
    use_not_allowed_methods(client, Route.delete, [client.put, client.patch])


def test_404(client):
    for _ in range(10):
        url = generate_random_url()
        response = client.get(url)
        assert_equals(response, 404)


def test_upload_without_file(client):
    use_not_allowed_methods(client, Route.upload, client.post, json_response_code=400)


def test_downloading_non_existing_hash(client):
    fake_hash = "x" * HASH_LENGTH
    response = client.get(Route.download, data={"hash": fake_hash})
    assert_equals(response, 404)


def test_download_invalid_hashes(client):
    for invalid_hash in get_invalid_hashes():
        response = client.get(Route.download, data={"hash": invalid_hash})
        assert_equals(response, 403)


def test_upload_text_stream(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()

    try:
        data = {'file': (get_test_bytes_object(), test_file_name)}
        response = client.post(Route.upload, data=data)
        json_response = assert_equals(response, 200)
        assert "hash" in json_response.keys()
    finally:
        remove_test_file()


def test_upload_empty_stream(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()

    try:
        file_name = test_file_name.split('.')[0]
        data = {'file': (get_test_bytes_object(empty_content=True), file_name)}
        response = client.post(Route.upload, data=data)
        json_response = assert_equals(response, 403)
        assert "hash" not in json_response.keys()
    finally:
        remove_test_file()


def test_uploading_file_twice(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()
    try:
        fileIO, close_IO = get_uncloseable_bytes()
        data = {'file': (fileIO, test_file_name)}
        first_response = client.post(Route.upload, data=data)

        assert_equals(first_response, 200)

        fileIO.seek(0)
        response = client.post(Route.upload, data=data)

        json_response = assert_equals(response, 400)
        assert "hash" not in json_response.keys()

    finally:
        close_IO()
        remove_test_file()


def test_file_content_is_the_same(client):
    # File won't be uploaded if it's already on the disk
    remove_test_file()
    response = None
    try:
        fileIO, close_IO = get_uncloseable_bytes()
        response_upload = client.post(Route.upload, data={'file': (fileIO, test_file_name)})

        assert_equals(response_upload, 200)
        fileIO.seek(0)
        response = client.get(Route.download, data={"hash": response_upload.get_json()["hash"]})
        assert response.data == fileIO.read()
        assert response.status_code == 200

    finally:
        # remove link to bytes in order to delete file on disk after test
        del response
        close_IO()
        remove_test_file()


def test_delete_invalid_hashes(client):
    for invalid_hash in get_invalid_hashes():
        response = client.get(Route.delete, data={"hash": invalid_hash})
        assert_equals(response, 403)


def test_delete_non_existing_hash(client):

    hash = "x" * HASH_LENGTH
    response = client.get(Route.delete, data={"hash": hash})
    assert_equals(response, 404)


def test_delete_existing_hash(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()
    try:
        fileIO, close_IO = get_uncloseable_bytes()
        response_upload = client.post(Route.upload, data={'file': (fileIO, test_file_name)})
        json_response = assert_equals(response_upload, 200)
        uploaded_hash = json_response["hash"]

        response_download = client.get(Route.download, data={"hash": uploaded_hash})

        fileIO.seek(0)

        assert response_download.status_code == 200
        assert response_download.data == fileIO.read()

        # Assert that file cannot be deleted if there is somebody
        # Who is still connected to it
        # Connection to the file is stored in response_download.data

        response = client.get(Route.delete, data={"hash": uploaded_hash})
        assert_equals(response, 500)

        del response_download

        # Since the connection is no longer stored
        # We assert that the file can be deleted

        response = client.get(Route.delete, data={"hash": uploaded_hash})
        assert_equals(response, 200)

        # File is not available anymore

        response_download_after = client.get(Route.download, data={"hash": uploaded_hash})
        assert_equals(response_download_after, 404)

    finally:
        close_IO()
        remove_test_file()

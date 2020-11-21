import pytest
import requests
import string
import random
import io
import os

from flask import Response, url_for
from pytest_flask.plugin import JSONResponse
import json


from app import create_app
from config import HASH_LENGTH, STORAGE_DIR, TEMP_DIR

from typing import List, Callable, Optional, Union, Dict, BinaryIO, Tuple

URL = '/'

real_urls = ('/', '/upload', '/download', '/delete')

test_bytes = b"some initial text data"


def generate_random_url():
    symbols = string.ascii_lowercase + '/1234567890'
    fake_url = ''.join(random.choice(symbols) for s in range(len(symbols)+1))
    if fake_url not in real_urls:
        return fake_url
    else:
        return generate_random_url()


def url(*paths, **arguments) -> str:
    base = "/".join(paths)
    if arguments:
        return f"{base}?{'&'.join(set(arguments.items()))}"
    return base


# @pytest.fixture
# def app():
#     app = create_app()
#     return app

@pytest.fixture(scope='module')
def client():
    flask_app = create_app()
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()


def assert_equals(client, url: str, status_code: int):
    response = client.get(url)
    json_response = response.get_json()

    assert response.status_code == status_code
    assert "message" in json_response.keys()
    assert "status_code" in json_response.keys()
    assert json_response["status_code"] == status_code


def test_root_get(client):

    assert_equals(client, '/', 200)


def post(client, url: str, **kw):
    return client.post(url,  data=json.dumps(kw), content_type='application/json')


def send_request(client, url: str, not_allowed_methods: Union[Callable, List[Callable]], json_response_code: Optional[int] = None, **data: Optional[Dict]):

    json_response_code = json_response_code or 405
    data = json.dumps({"some": "data"}) if not len(data) else data

    if not isinstance(not_allowed_methods, (list, tuple, set)):
        not_allowed_methods = [not_allowed_methods]

    for method in not_allowed_methods:

        response = method(url, data=data, content_type='application/json')
        json_response = response.get_json()

        print(json_response)

        assert response.status_code == json_response_code
        assert "message" in json_response.keys()
        assert "status_code" in json_response.keys()
        assert json_response["status_code"] == json_response_code


def test_root_post(client):
    send_request(client, '/', [client.post, client.put, client.delete, client.patch])


def test_upload_invalid(client):
    send_request(client, '/upload', [client.get, client.delete, client.patch])


def test_download_invalid(client):
    send_request(client, '/download', [client.post, client.put, client.delete, client.patch])


def test_delete_invalid(client):
    send_request(client, '/delete', [client.put, client.patch])


def test_not_found(client):
    for _ in range(10):
        assert_equals(client, generate_random_url(), 404)


def test_upload_without_file(client):
    send_request(client, '/upload', client.post, json_response_code=400)


def test_downloading_non_existing_hash(client):

    hash = "a" * HASH_LENGTH
    response = client.get(f'/download?hash={hash}')
    json_response = response.get_json()

    assert response.status_code == 404
    assert "message" in json_response.keys()
    assert json_response["status_code"] == 404


def get_invalid_hashes() -> List[str]:

    return (str(h) for h in ("/#)$(*^)", ")(*+_~!2:)", "a"
                             * (HASH_LENGTH-1), "a" * (HASH_LENGTH * 2), " ", "a" * (2**10)))


def get_test_bytes_object(content: Optional[bytes] = None, empty_content: Optional[bool] = False) -> BinaryIO:
    content = test_bytes or content
    content = b"" if empty_content else content
    return io.BytesIO(content)


def test_download_invalid_hashes(client):
    for invalid_hash in get_invalid_hashes():
        response = client.get('/download', data={"hash": invalid_hash})
        json_response = response.get_json()
        print(json_response)
        assert response.status_code == 403
        assert "message" in json_response.keys()
        assert json_response["status_code"] == 403


def remove_test_file():
    # try:
    file_path = os.path.join(STORAGE_DIR, '4d', '4d0e3bddc298dd5e758dfe682fe964db045af1f827b6a5501ffb9fb0ad9c4b31.txt')
    file_dir_path = os.path.dirname(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    # if os.path.exists(file_dir_path):
    #     if not os.listdir(file_dir_path):
    #         os.rmdir(file_dir_path)

    file_path_temp = os.path.join(STORAGE_DIR, TEMP_DIR, "fake-text-stream.txt")
    if os.path.exists(file_path_temp):
        os.remove(file_path_temp)
    # except PermissionError:
    #     print("Are you win user? SBT")


def test_upload_text_stream(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()

    try:
        file_name = "fake-text-stream.txt"
        data = {
            'file': (get_test_bytes_object(), file_name)
        }
        response = client.post('/upload', data=data)
        json_response = response.get_json()
        print(json_response)
        assert response.status_code == 200
        assert "message" in json_response.keys()
        assert "hash" in json_response.keys()
        assert json_response["status_code"] == 200
    finally:
        remove_test_file()


def test_upload_empty_stream(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()

    try:
        file_name = "fake-empty-stream"
        data = {
            'file': (get_test_bytes_object(empty_content=True), file_name)
        }
        response = client.post('/upload', data=data)
        json_response = response.get_json()
        print(json_response)
        assert response.status_code == 403
        assert "message" in json_response.keys()
        assert "hash" not in json_response.keys()
        assert json_response["status_code"] == 403
    finally:
        remove_test_file()


def get_uncloseable_bytes() -> Tuple[BinaryIO, Callable]:
    """Short summary.

    Returns:
        Tuple[BinaryIO, Callable]: .

    Raises:
        ExceptionName: Why the exception is raised.

    """
    fileIO = get_test_bytes_object()
    close = fileIO.close
    fileIO.close = lambda: None
    return fileIO, close


def test_uploading_file_twice(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()
    try:
        file_name = "fake-text-stream.txt"
        fileIO, close_IO = get_uncloseable_bytes()
        data = {
            'file': (fileIO, file_name)
        }

        client.post('/upload', data=data)

        fileIO.seek(0)

        response = client.post('/upload', data=data)
        json_response = response.get_json()

        assert response.status_code == 400
        assert "message" in json_response.keys()
        assert "hash" not in json_response.keys()
        assert json_response["status_code"] == 400
    finally:
        close_IO()
        remove_test_file()


def test_file_remains_the_same(client):
    # File won't be uploaded if it's already on the disk
    remove_test_file()
    response = None
    try:
        file_name = "fake-text-stream.txt"
        fileIO, close_IO = get_uncloseable_bytes()

        post_response = client.post('/upload', content_type='multipart/form-data',
                                    data={'file': (fileIO, file_name)})

        assert post_response.status_code == 200
        fileIO.seek(0)
        response = client.get('/download', data={"hash": post_response.get_json()["hash"]})
        assert response.data == fileIO.read()
        assert response.status_code == 200

    finally:
        # remove link to bytes in order to delete file on disk after test
        del response
        close_IO()
        remove_test_file()


def test_delete_invalid_hashes(client):
    for invalid_hash in get_invalid_hashes():
        response = client.get('/delete', data={"hash": invalid_hash})
        json_response = response.get_json()
        print(json_response)
        assert response.status_code == 403
        assert "message" in json_response.keys()
        assert json_response["status_code"] == 403


def test_delete_non_existing_hash(client):

    hash = "a" * HASH_LENGTH
    response = client.get('/delete', data={"hash": hash})
    json_response = response.get_json()

    assert response.status_code == 404
    assert "message" in json_response.keys()
    assert json_response["status_code"] == 404


def test_delete_existing_hash(client):

    # File won't be uploaded if it's already on the disk
    remove_test_file()
    try:
        file_name = "fake-text-stream.txt"
        fileIO, close_IO = get_uncloseable_bytes()

        post_response = client.post('/upload', content_type='multipart/form-data',
                                    data={'file': (fileIO, file_name)})

        assert post_response.status_code == 200

        uploaded_hash = post_response.get_json()["hash"]

        response_download = client.get('/download', data={"hash": uploaded_hash})

        fileIO.seek(0)

        assert response_download.status_code == 200
        assert response_download.data == fileIO.read()

        # Assert that we cannot delete file while there is somebody
        # That still connected to it

        response = client.get('/delete', data={"hash": uploaded_hash})
        json_response = response.get_json()
        assert response.status_code == 500
        assert "message" in json_response.keys()
        assert json_response["status_code"] == 500

        del response_download
        # Now after deleting link to the file
        # We assert that thus nobody is connected to it now
        # It can be deleted
        response = client.get('/delete', data={"hash": uploaded_hash})
        json_response = response.get_json()
        assert response.status_code == 200
        assert "message" in json_response.keys()
        assert json_response["status_code"] == 200

        response_download_after = client.get('/download', data={"hash": uploaded_hash})

        assert response_download_after.status_code == 404
        assert response_download_after.data

    finally:

        # double check in case of AssertionError
        close_IO()
        remove_test_file()

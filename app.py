import os
import logging
import sys
import hashlib
import traceback
import re


import flask
from flask import Flask, jsonify, make_response, send_from_directory
from flask_restful import Resource, Api, reqparse
import ast
import werkzeug
from werkzeug.utils import secure_filename
import shutil

from typing import Tuple, Dict, Optional, Any

from database import Database


def encrypt_string(unhashed_string: str, raw: Optional[bool] = False) -> str:
    if not isinstance(unhashed_string, str):
        raise ValueError("Please provide string argument")
    hashed = hashlib.sha256(unhashed_string.encode('utf-8'))
    return hashed if raw else hashed.hexdigest()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, 'storage')
TEMP_DIR = os.path.join(BASE_DIR, 'tmp')
SRC_DIR = os.path.join(BASE_DIR, 'src')
HASH_LENGTH = len(encrypt_string('hashed string'))


def verify_hash(hash_string: str) -> bool:
    print(len(hash_string), HASH_LENGTH)
    return len(hash_string) == HASH_LENGTH and re.match(r"^[\w\d_-]*$", hash_string)


for directory in [STORAGE_DIR, TEMP_DIR, SRC_DIR]:
    if not os.path.exists(directory):
        os.mkdir(directory)


app = Flask(__name__)
api = Api(app)

# max file size is 2 gigabytes
app.config['MAX_CONTENT_LENGTH'] = 2 ** 64
app.config['DATABASE'] = os.path.join(SRC_DIR, 'db.db')
app.config['APP_NAME'] = "Hash Guard"

app.app_context().push()

db = Database()


class EmptyFileException(Exception):
    pass


class Responses:

    NotAllowed = "This method is not allowed. Please use {method} instead"

    Help = {"message": f"Welcome to {app.config['APP_NAME']}", "status_code": 200}

    Response403 = {"message": "Invalid hash", "status_code": 403}, 403
    Response404 = {"message": "Not found", "status_code": 404}, 404
    Response405 = {"message": "Only POST method is allowed", "status_code": 405}, 405
    Response406 = {"message": "Hash is too long", "status_code": 406}, 406
    Response413 = {"message": "Max file size is 2GB", "status_code": 413}, 413
    Response418 = {"message": "Good try. But I'm a teapot", "status_code": 418}, 418
    Response500 = {"message": "Sorry, there had been internal error", "status_code": 500}, 500

    @staticmethod
    def Build(status_code: int = 200, **kw) -> Tuple[Dict, int]:
        return {**kw, "status_code": status_code}, status_code


StandartResponse = Tuple[Dict, int]


class BaseRequest(Resource):
    """Base Resource class
        Returns 'method not allowed' at every method
    """

    AllowedMethod = ""

    def GetParameter(self, parameter_name: str, required: Optional[bool] = False, **kw: Any):
        """Lightweight interface to get parameter from json body

        Args:
            parameter_name (str): parameter from json body of the request
            required (Optional[bool]): . Defaults to False.
                We prefer to set parameters as non-required
                to be able to overwrite default missing json-body parameter
                Flask response which missed the status_code filed
            **kw (Any): Any settings to reqparse.RequestParser().add_argument()

        Returns:
            type: parameter from json body of the request

        Raises:
            ExceptionName: Why the exception is raised.

        """
        parser = reqparse.RequestParser()
        parser.add_argument(parameter_name, **kw, required=required)
        args = parser.parse_args()
        return args[parameter_name]

    def NotAllowed(self) -> StandartResponse:
        return Responses.Build(message=Responses.NotAllowed.format(method=self.AllowedMethod), status_code=405)

    def get(self, *args, **kw):
        return self.NotAllowed()

    def post(self, *args, **kw):
        return self.NotAllowed()

    def put(self, *args, **kw):
        return self.NotAllowed()

    def patch(self, *args, **kw):
        return self.NotAllowed()

    def delete(self, *args, **kw):
        return self.NotAllowed()

    def copy(self, *args, **kw):
        return self.NotAllowed()


class StorageMaster:

    BUF_SIZE = 65536  # 64kb

    def check_directory_exists():
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

    def get_hash(file_path: str) -> str:
        sha2 = hashlib.sha256()
        sha2.update(file_path.encode('utf-8'))
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(StorageMaster.BUF_SIZE)
                if not data:
                    break
                sha2.update(data)

        return sha2.hexdigest()

    @classmethod
    def save(cls, f: werkzeug.datastructures.FileStorage) -> str:

        cls.check_directory_exists()

        original_name = secure_filename(f.filename)
        temp_path = os.path.join(TEMP_DIR, original_name)
        f.save(temp_path)

        if not os.stat(temp_path).st_size:
            os.remove(temp_path)
            raise EmptyFileException()

        hash_string = cls.get_hash(temp_path)

        directory = os.path.join(STORAGE_DIR, hash_string[:2])

        if not os.path.exists(directory):
            os.mkdir(directory)

        file_extension = os.path.splitext(temp_path)[1]
        hashed_path = os.path.join(directory, hash_string + file_extension)

        if not os.path.exists(hashed_path):
            shutil.move(temp_path, hashed_path)
        else:
            raise FileExistsError()

        return hash_string

    @classmethod
    def get(cls, hash_string: str) -> str:
        print(hash_string)
        seek_directory = os.path.join(STORAGE_DIR, hash_string[:2])

        print(seek_directory)

        if os.path.exists(seek_directory):
            for suspect in os.listdir(seek_directory):
                filename, extension = os.path.splitext(suspect)
                if filename == hash_string:
                    return suspect
        return None

    @classmethod
    def delete(cls, file_name: str) -> str:
        if not os.path.isabs(file_name):
            file_path = os.path.join(STORAGE_DIR, file_name[:2], file_name)
        else:
            file_path = file_name
        print(file_path)

        # double check
        if os.path.exists(file_path):
            os.remove(file_path)
            directory = os.path.dirname(file_path)
            if not os.listdir(directory):
                os.rmdir(directory)


class UploadRequest(BaseRequest):

    AllowedMethod = "POST"

    def post(self, *args, **kw):

        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        file = args['file']

        if not file:
            return Responses.Build(message="Please provide file to upload in form-data with a key 'file'", status_code=400)

        try:
            hash_string = StorageMaster.save(file)
        except FileExistsError:
            return Responses.Build(message="File you are trying to upload is already on the disk", status_code=400)
        except EmptyFileException:
            return Responses.Build(message="Empty file discarded", status_code=403)


        return Responses.Build(message="File succesfully uploaded", hash=hash_string, status_code=200)

    def put(self, *args, **kw):
        return self.post()


class DownloadRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, *args, **kw):

        hash_string = kw.get('hash') or self.GetParameter('hash', type=str)

        if not hash_string:
            return Responses.Build(message="Wrong usage. Please provide file hash to download it", status_code=400)

        if not verify_hash(hash_string):
            return Responses.Response403

        foundfile = StorageMaster.get(hash_string)
        if foundfile:
            return send_from_directory(STORAGE_DIR, foundfile, as_attachment=True)

        return Responses.Build(message="Sorry, hash not found on the server", status_code=404)


class TeaPotRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, *args, **kw):
        return Responses.Response418


class DeleteRequest(BaseRequest):

    AllowedMethod = "GET, POST or DELETE"

    def get(self, *args, **kw):

        hash_string = self.GetParameter('hash', type=str)
        if not hash_string:
            return Responses.Build(message="Wrong usage. Please provide file hash to delete it", status_code=400)

        if not verify_hash(hash_string):
            return Responses.Response403

        file_path = StorageMaster.get(hash_string)

        if file_path:
            StorageMaster.delete(file_path)
            return Responses.Build(message="File was deleted", status_code=200)

        return Responses.Build(message="Sorry, hash not found on the server", status_code=404)

    def post(self, *args, **kw):
        return self.get()

    def delete(self, *args, **kw):
        return self.get()


class DefaultRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, *args, **kw):
        return Responses.Help

# @app.route('')
# def get(*args, **kw):
#     return Responses.Response418


api.add_resource(DefaultRequest, '/')
api.add_resource(UploadRequest, '/upload')
api.add_resource(DownloadRequest, '/download')
api.add_resource(DeleteRequest, '/delete', '/delete/<string:hash>')
api.add_resource(TeaPotRequest, '/admin', '/admin/<string:anything>')


@app.errorhandler(404)
def not_found(error):
    return Responses.Response404


@app.errorhandler(413)
def request_entity_too_large(error):
    # This one doesn't work for some reason
    return Responses.Response413


def default_handler(error):

    print(traceback.format_exc())

    if isinstance(error, werkzeug.exceptions.HTTPException):
        return Responses.Build(message=str(error), status_code=error.code)

    return Responses.Response500


# db = Database(app)

app.config['TRAP_HTTP_EXCEPTIONS'] = True
app.register_error_handler(Exception, default_handler)


db.init_db()
db.init_app(app)

# db.init_app(app)
# @app.teardown_request
# def teardown_request(e):
#     db.close()

if __name__ == '__main__':
    app.run(host='localhost', debug=True)

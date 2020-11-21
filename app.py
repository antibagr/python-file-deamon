import os
import logging
import sys
import hashlib
import traceback


import flask
from flask import Flask, jsonify, make_response, send_from_directory
from flask_restful import Resource, Api, reqparse
import ast
import werkzeug
from werkzeug.utils import secure_filename
import shutil

from typing import Tuple, Dict, Optional

from database import Database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, 'storage')
TEMP_DIR = os.path.join(BASE_DIR, 'tmp')
SRC_DIR = os.path.join(BASE_DIR, 'src')

for directory in [STORAGE_DIR, TEMP_DIR, SRC_DIR]:
    if not os.path.exists(directory):
        os.mkdir(directory)


app = Flask(__name__)
api = Api(app)

# max file size is 2 gigabytes
app.config['MAX_CONTENT_LENGTH'] = 2 ** 64
app.config['DATABASE'] = os.path.join(SRC_DIR, 'db.db')

app.app_context().push()

db = Database()


class Responses:

    NotAllowed = "This method is not allowed. Please use {method} instead"

    Response404 = {"message": "Not found", "status_code": 404}, 404
    Response405 = {"message": "Only POST method is allowed", "status_code": 405}, 405
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

    BUF_SIZE = 65536 # 64kb

    def check_directory_exists():
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

    def get_hash(file_path: str) -> str:
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(StorageMaster.BUF_SIZE)
                if not data:
                    break
                sha1.update(data)

        return sha1.hexdigest()

    @classmethod
    def save(cls, f: werkzeug.datastructures.FileStorage) -> str:

        cls.check_directory_exists()

        original_name = secure_filename(f.filename)
        temp_path = os.path.join(TEMP_DIR, original_name)
        f.save(temp_path)

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
    def get(hash_string: str) -> str:
        seek_directory = os.path.join(STORAGE_DIR, hash_string[:2])
        if os.path.exists(seek_directory):
            for suspect in os.listdir(seek_directory):
                filename, extension = os.path.splitext(suspect)
                if filename == hash_string:
                    return suspect
        return None


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

        return Responses.Build(message="File succesfully uploaded", hash=hash_string, status_code=200)

    def put(self, *args, **kw):
        return self.post()


class DownloadRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, hash: Optional[str] = None, *args, **kw):
        if not hash:
            return Responses.Build(message="Wrong usage. Please provide file hash to download it", status_code=400)

        foundfile = StorageMaster.get(hash)
        if foundfile:
            return send_from_directory(STORAGE_DIR, foundfile, as_attachment=True)

        return Responses.Build(message="Sorry, hash not found on the server", status_code=404)


class TeaPotRequest(BaseRequest):

    def get(self, *args, **kw):
        return Responses.Response418

# 63d50cb0b361543178bc1f838fc562e973ec3f71
#     def post(self):
#         pass
#         # raise InvalidUsage('Only GET method is allowed', status_code=405)
#
#     #     parser = reqparse.RequestParser()  # initialize parser
#     #     parser.add_argument('locationId', required=True, type=int)  # add args
#     #     parser.add_argument('name', required=True)
#     #     parser.add_argument('rating', required=True)
#     #     args = parser.parse_args()  # parse arguments to dictionary
#     #
#     #     # read our CSV
#     #     data = pd.read_csv('locations.csv')
#     #
#     #     # check if location already exists
#     #     if args['locationId'] in list(data['locationId']):
#     #         # if locationId already exists, return 401 unauthorized
#     #         return {
#     #             'message': f"'{args['locationId']}' already exists."
#     #         }, 409
#     #     else:
#     #         # otherwise, we can add the new location record
#     #         # create new dataframe containing new values
#     #         new_data = pd.DataFrame({
#     #             'locationId': [args['locationId']],
#     #             'name': [args['name']],
#     #             'rating': [args['rating']]
#     #         })
#     #         # add the newly provided values
#     #         data = data.append(new_data, ignore_index=True)
#     #         data.to_csv('locations.csv', index=False)  # save back to CSV
#     #         return {'data': data.to_dict()}, 200  # return data with 200 OK
#     #
#     # def patch(self):
#     #     parser = reqparse.RequestParser()  # initialize parser
#     #     parser.add_argument('locationId', required=True, type=int)  # add args
#     #     parser.add_argument('name', store_missing=False)  # name/rating are optional
#     #     parser.add_argument('rating', store_missing=False)
#     #     args = parser.parse_args()  # parse arguments to dictionary
#     #
#     #     # read our CSV
#     #     data = pd.read_csv('locations.csv')
#     #
#     #     # check that the location exists
#     #     if args['locationId'] in list(data['locationId']):
#     #         # if it exists, we can update it, first we get user row
#     #         user_data = data[data['locationId'] == args['locationId']]
#     #
#     #         # if name has been provided, we update name
#     #         if 'name' in args:
#     #             user_data['name'] = args['name']
#     #         # if rating has been provided, we update rating
#     #         if 'rating' in args:
#     #             user_data['rating'] = args['rating']
#     #
#     #         # update data
#     #         data[data['locationId'] == args['locationId']] = user_data
#     #         # now save updated data
#     #         data.to_csv('locations.csv', index=False)
#     #         # return data and 200 OK
#     #         return {'data': data.to_dict()}, 200
#     #
#     #     else:
#     #         # otherwise we return 404 not found
#     #         return {
#     #             'message': f"'{args['locationId']}' location does not exist."
#     #         }, 404
#     #
#     # def delete(self):
#     #     parser = reqparse.RequestParser()  # initialize parser
#     #     parser.add_argument('locationId', required=True, type=int)  # add locationId arg
#     #     args = parser.parse_args()  # parse arguments to dictionary
#     #
#     #     # read our CSV
#     #     data = pd.read_csv('locations.csv')
#     #
#     #     # check that the locationId exists
#     #     if args['locationId'] in list(data['locationId']):
#     #         # if it exists, we delete it
#     #         data = data[data['locationId'] != args['locationId']]
#     #         # save the data
#     #         data.to_csv('locations.csv', index=False)
#     #         # return data and 200 OK
#     #         return {'data': data.to_dict()}, 200
#     #
#     #     else:
#     #         # otherwise we return 404 not found
#     #         return {
#     #             'message': f"'{args['locationId']}' location does not exist."
#     #         }
#
#


class DeleteRequest(BaseRequest):
    pass


class DefaultRequest(Resource):
    def get(self):
        return {'hello': 'world'}

# @app.route('')
# def get(*args, **kw):
#     return Responses.Response418


api.add_resource(DefaultRequest, '/')
api.add_resource(UploadRequest, '/upload')
api.add_resource(DownloadRequest, '/download/<string:hash>', '/download/')
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

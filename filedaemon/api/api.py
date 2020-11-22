import os

from flask import send_from_directory
from flask_restful import reqparse
from werkzeug.datastructures import FileStorage
from werkzeug import exceptions

from .model import BaseRequest, Responses, StandartResponse
from storage import StorageMaster, EmptyFileException
from utils import verify_hash
from config import STORAGE_DIR


class UploadRequest(BaseRequest):

    AllowedMethod = "POST"

    def post(self, **kw) -> StandartResponse:

        parse = reqparse.RequestParser()
        parse.add_argument('file', type=FileStorage, location='files')
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

    def put(self, **kw) -> StandartResponse:
        return self.post()


class DownloadRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, **kw) -> StandartResponse:

        hash_string = kw.get('hash') or self.GetParameter('hash', type=str)

        if not hash_string:
            return Responses.Build(message="Wrong usage. Please provide file hash to download it", status_code=400)

        if not verify_hash(hash_string):
            return Responses.Response403

        found_dir, found_file = StorageMaster.get(hash_string)
        if found_file:

            try:
                return send_from_directory(os.path.join(STORAGE_DIR, found_dir), found_file, as_attachment=True)
            except exceptions.NotFound:
                # handle not found exception as internal
                # because if everything works just fine
                # this should not happen ever
                return Responses.Response500

        return Responses.Build(message="Sorry, hash not found on the server", status_code=404)


class TeaPotRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, **kw) -> StandartResponse:
        return Responses.Response418


class DeleteRequest(BaseRequest):

    AllowedMethod = "GET, POST or DELETE"

    def get(self, **kw) -> StandartResponse:

        hash_string = self.GetParameter('hash', type=str)
        if not hash_string:
            return Responses.Build(message="Wrong usage. Please provide file hash to delete it", status_code=400)

        if not verify_hash(hash_string):
            return Responses.Response403

        found_dir, found_file = StorageMaster.get(hash_string)

        if found_file:
            try:
                StorageMaster.delete(found_file)
            except PermissionError:
                return Responses.Build(message="Sorry, cannot delete the file now. Somebody is still connected to it", status_code=500)
            return Responses.Build(message="File was deleted", status_code=200)

        return Responses.Build(message="Sorry, hash not found on the server", status_code=404)

    def post(self, **kw) -> StandartResponse:
        return self.get()

    def delete(self, **kw) -> StandartResponse:
        return self.get()


class DefaultRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, **kw) -> StandartResponse:
        return Responses.Help
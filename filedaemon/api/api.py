import os

from flask import send_from_directory
from flask_restful import reqparse
from werkzeug.datastructures import FileStorage
from werkzeug import exceptions

from .abs import BaseRequest, Responses, StandartResponse, ResponseBuilder
from storage.manager import StorageMaster, EmptyFileException
from utils.encryption import verify_hash
from config import STORAGE_DIR


class UploadRequest(BaseRequest):

    AllowedMethod = "POST"

    def post(self, **kw) -> StandartResponse:
        """
        Requires:
            A file in form-data
        Returns:
            400 - file was not provided
            400 - file is already on the disk
            403 - empty file discarded
            200 - eile succesfully uploaded

        """

        file = self.GetParameter('file', type=FileStorage, location='files')

        if not file:
            return ResponseBuilder()(message="Please provide file to upload in a form-data with a key 'file'", status_code=400)

        try:
            hash_string = StorageMaster.save(file)
        except FileExistsError:
            return ResponseBuilder()(message="File you are trying to upload is already on the disk", status_code=400)
        except EmptyFileException:
            return ResponseBuilder()(message="Empty file discarded", status_code=403)

        return ResponseBuilder()(message="File succesfully uploaded", hash=hash_string, status_code=200)

    def put(self, **kw) -> StandartResponse:
        return self.post()


class DownloadRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, **kw) -> StandartResponse:
        """
        Requires:
            A hash in "hash" field
        Returns:
            400 - hash was not provided
            403 - invalid hash
            404 - file was not found
            500 - file was found but can't be sent

            file as as attachment if it's found

        """

        hash_string = kw.get('hash') or self.GetParameter('hash', type=str)

        if not hash_string:
            return ResponseBuilder()(message="Wrong usage. Please provide file hash to download it", status_code=400)

        if not verify_hash(hash_string):
            return Responses.Response403

        found_file = StorageMaster.get(hash_string)
        if found_file:

            try:
                return send_from_directory(os.path.join(STORAGE_DIR, found_file[:2]), found_file, as_attachment=True)
            except exceptions.NotFound:
                # handle not found exception as internal
                # because if everything works just fine
                # this should not happen ever
                return Responses.Response500

        return ResponseBuilder()(message="Sorry, hash not found on the server", status_code=404)


class TeaPotRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, **kw) -> StandartResponse:
        return Responses.Response418


class DeleteRequest(BaseRequest):

    AllowedMethod = "GET, POST or DELETE"

    def get(self, **kw) -> StandartResponse:
        """
        Requires:
            A hash in "hash" field
        Returns:
            400 - hash was not provided
            403 - invalid hash
            404 - file was not found
            200 - file was deleted
            500 - PermissonError (only happens when running on windows)

        """

        hash_string = self.GetParameter('hash', type=str)
        if not hash_string:
            return ResponseBuilder()(message="Wrong usage. Please provide file hash to delete it", status_code=400)

        if not verify_hash(hash_string):
            return Responses.Response403

        found_file = StorageMaster.get(hash_string)

        if found_file:
            try:
                StorageMaster.delete(found_file)
            except PermissionError:
                return ResponseBuilder()(message="Sorry, cannot delete the file now. Somebody is still connected to it", status_code=500)
            return ResponseBuilder()(message="File was deleted", status_code=200)

        return ResponseBuilder()(message="Sorry, hash not found on the server", status_code=404)

    def post(self, **kw) -> StandartResponse:
        return self.get()

    def delete(self, **kw) -> StandartResponse:
        return self.get()


class DefaultRequest(BaseRequest):

    AllowedMethod = "GET"

    def get(self, **kw) -> StandartResponse:
        return Responses.Help

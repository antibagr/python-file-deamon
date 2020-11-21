import os

import shutil
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import STORAGE_DIR, TEMP_DIR, HASHING_METHOD, READING_FILE_BUF_SIZE


class EmptyFileException(Exception):
    pass


class StorageMaster:

    def check_directory_exists():
        if not os.path.exists(TEMP_DIR):
            os.mkdir(TEMP_DIR)

    def get_hash(file_path: str) -> str:
        sha2 = HASHING_METHOD()
        sha2.update(file_path.encode('utf-8'))
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(READING_FILE_BUF_SIZE)
                if not data:
                    break
                sha2.update(data)

        return sha2.hexdigest()

    @classmethod
    def save(cls, f: FileStorage) -> str:

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

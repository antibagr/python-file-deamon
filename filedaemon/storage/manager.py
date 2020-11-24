import os
from functools import partial, wraps


import shutil
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config import STORAGE_DIR, TEMP_DIR, HASHING_METHOD, READING_FILE_BUF_SIZE

from typing import Tuple, Callable, Any, List


class EmptyFileException(Exception):
    """
    Raised if storing empty files is not allowed
    """

    def __init__(self):
        self.message = "Storing empty files is not allowed"
        super().__init__()


def check_directory_exists(f: Callable, dirs: List[str]) -> Callable:
    """
    Decorator that checks every directory in passed dirs and create any
    that doesn't exist

    f: Callable - funciton to be decotared
    dirs: List[str] - list of directories to be checked
    """

    @wraps(f)
    def wrapper(*args: Any, **kw: Any) -> Any:
        for d in dirs:
            if not os.path.exists(d):
                os.mkdir(d)
        return f(*args, **kw)
    return wrapper


class StorageMaster(object):
    """
    Class to operate file-related process
    Stores, receives and deletes files in directory
    defined in cls.STORAGE
    """

    STORAGE: str = STORAGE_DIR
    TEMP: str = TEMP_DIR
    check_directory_decorator: Callable = partial(check_directory_exists, dirs=[STORAGE, TEMP])

    @classmethod
    @check_directory_decorator
    def save(cls, f: FileStorage, fastway=True) -> str:
        """
        Saving file and computing it's hash at the same stream
        """

        if f.stream.read(1) == b'':
            raise EmptyFileException()

        f.stream.seek(0)

        f.filename = secure_filename(f.filename)

        hash_instance = HASHING_METHOD()
        hash_instance.update(f.filename.encode('utf-8'))
        temp_path = os.path.join(cls.TEMP, f.filename)
        with open(temp_path, "wb", buffering=READING_FILE_BUF_SIZE, closefd=True) as out_file:

            while True:
                data = f.stream.read(READING_FILE_BUF_SIZE)
                if not data:
                    break
                hash_instance.update(data)
                out_file.write(data)

        hash_string = hash_instance.hexdigest()

        directory = os.path.join(cls.STORAGE, hash_string[:2])

        if not os.path.exists(directory):
            os.mkdir(directory)

        file_extension = os.path.splitext(temp_path)[1]
        hashed_path = os.path.join(directory, hash_string + file_extension)

        if not os.path.exists(hashed_path):
            try:
                shutil.move(temp_path, hashed_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        else:
            raise FileExistsError()

        return hash_string

    @classmethod
    @check_directory_decorator
    def get(cls, hash_string: str) -> Tuple[str, str]:
        """
        Get subdirectory and full filename if one is found
        """

        seek_directory = os.path.join(cls.STORAGE, hash_string[:2])

        if os.path.exists(seek_directory):
            for suspect in os.listdir(seek_directory):
                filename, extension = os.path.splitext(suspect)
                if filename == hash_string:
                    return hash_string[:2], suspect
        return None, None

    @classmethod
    @check_directory_decorator
    def delete(cls, file_name: str) -> str:
        """
        Deletes file if one is found.
        If it's the last file in the directory it wiil be cleared too
        """

        if not os.path.isabs(file_name):
            file_path = os.path.join(cls.STORAGE, file_name[:2], file_name)
        else:
            file_path = file_name

        # double check
        if os.path.exists(file_path):
            os.remove(file_path)
            directory = os.path.dirname(file_path)
            if not os.listdir(directory):
                os.rmdir(directory)

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

    @staticmethod
    def check_file_is_not_empty(f: FileStorage) -> None:
        """
        Raises EmptyFileException if file is empty
        """

        if f.stream.read(1) == b'':
            raise EmptyFileException()
        f.stream.seek(0)

    @classmethod
    def _save_file_on_disk(cls, f: FileStorage) -> str:
        """
        Save file to temp directory and compute its hash at the same stream

        Args:
            f: FileStorage - file to be stored
        Returns:
            str - computed hash
        """

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

        return hash_instance.hexdigest()

    @classmethod
    def _move_file_from_temp(cls, temp_path: str, hash_string: str) -> None:
        """Rename file given in temp_path and
        move it to its permanent storage defined in hash_string

        Args:
            temp_path (type): full path to file saved in temp directory
            hash_string (type): computed hash of the file

        Returns:
            None

        Raises:
            FileExistsError: If file with such name is already exists

        """
        directory = os.path.join(cls.STORAGE, hash_string[:2])

        if not os.path.exists(directory):
            os.mkdir(directory)

        file_extension = os.path.splitext(temp_path)[1]
        hashed_path = os.path.join(directory, hash_string + file_extension)

        try:
            if not os.path.exists(hashed_path):
                shutil.move(temp_path, hashed_path)
            else:
                raise FileExistsError()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


    @classmethod
    @check_directory_decorator
    def save(cls, f: FileStorage) -> str:
        """
        Save user's file and returns its hash

        Args:
            f (FileStorage): User's file

        Returns:
            str: computed hash

        Raises:
            EmptyFileException, FileExistsError, PermissionError
        """

        cls.check_file_is_not_empty(f)
        hash_string = cls._save_file_on_disk(f)
        temp_path = os.path.join(cls.TEMP, f.filename)
        cls._move_file_from_temp(temp_path, hash_string)

        return hash_string

    @classmethod
    @check_directory_decorator
    def get(cls, hash_string: str) -> str:
        """
        Get subdirectory and full filename if one is found
        """

        seek_directory = os.path.join(cls.STORAGE, hash_string[:2])

        if os.path.exists(seek_directory):
            for full_filename in os.listdir(seek_directory):
                filename, extension = os.path.splitext(full_filename)
                if filename == hash_string:
                    return full_filename
        return None

    @classmethod
    @check_directory_decorator
    def delete(cls, file_name: str) -> None:
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

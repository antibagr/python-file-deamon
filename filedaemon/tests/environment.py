import string
import random
import io
import os

from typing import List, Optional, BinaryIO, Tuple, Callable

from config import HASH_LENGTH, STORAGE_DIR, TEMP_DIR


real_urls = ('/', '/upload', '/download', '/delete')
test_bytes = b"some initial text data"
test_file_name = "fake-text-stream.txt"
testing_hash = '4d0e3bddc298dd5e758dfe682fe964db045af1f827b6a5501ffb9fb0ad9c4b31'


def generate_pseudo_word() -> str:
    return "".join([random.choice(string.ascii_lowercase) for _ in range(10)])


def generate_random_url() -> str:
    """
    Generate string sequense that
    Looks like a url
    """

    fake_url = '/'
    fake_url += '/'.join((generate_pseudo_word() for _ in range(3)))
    if fake_url not in real_urls:
        return fake_url
    else:
        return generate_random_url()


def get_invalid_hashes() -> List[str]:
    """
    Generate a list of invalid hashes
    """

    return (str(h) for h in ("/#)$(*^)", ")(*+_~!2:)", "x"
                             * (HASH_LENGTH-1), "x" * (HASH_LENGTH * 2), " ", "x" * (2**10)))


def get_test_bytes_object(content: Optional[bytes] = None, empty_content: Optional[bool] = False) -> BinaryIO:
    """Get binary object with test content
    Args:
        content (Optional[bytes]): Optional custom content
        empty_content (Optional[bool]): Should it return an empty binary?
    Returns:
        BinaryIO
    """
    content = test_bytes or content
    content = b"" if empty_content else content
    return io.BytesIO(content)


def get_uncloseable_bytes() -> Tuple[BinaryIO, Callable]:
    """
    Get uncloseable bytes object
    In order to control when it should be closed
    Returns:
        Tuple[BinaryIO, Callable]: A binary object and a function that closes it
    """
    fileIO = get_test_bytes_object()
    close = fileIO.close
    fileIO.close = lambda: None
    return fileIO, close


def remove_test_file():
    # try:
    file_path = os.path.join(STORAGE_DIR, '4d', f'{testing_hash}.txt')
    file_dir_path = os.path.dirname(file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    if os.path.exists(file_dir_path):
        if not os.listdir(file_dir_path):
            os.rmdir(file_dir_path)

    file_path_temp = os.path.join(STORAGE_DIR, TEMP_DIR, "fake-text-stream.txt")
    if os.path.exists(file_path_temp):
        os.remove(file_path_temp)
    # except PermissionError:
    #     print("Are you win user? SBT")

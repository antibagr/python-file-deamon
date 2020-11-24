import pytest

# from tests.environment import (generate_random_url, get_invalid_hashes,
#                                get_test_bytes_object, get_uncloseable_bytes,
#                                remove_test_file, test_file_name)

from storage.manager import StorageMaster, EmptyFileException


from utils.encryption import encrypt_string, verify_hash
from config import HASHING_METHOD, HASH_LENGTH
from tests.environment import generate_pseudo_word


def test_encrypt_string_value_error():

    with pytest.raises(ValueError):
        encrypt_string(123)
        encrypt_string(['not a string'])
        encrypt_string(object())


def test_encrypt_string():
    assert encrypt_string('testing string') == HASHING_METHOD(b'testing string').hexdigest()
    assert encrypt_string('testing string', raw=True) == HASHING_METHOD(b'testing string').digest()


def test_invalid_hashes_is_invalid():

    for invalid_hash in ['x' * (HASH_LENGTH - 1), 'C:', '/root/', ';DROP TABLE admin', (r'!@#$%^&*()_\?/ASdQWE!@#%&' * 10)[:HASH_LENGTH], ]:
        assert not verify_hash(invalid_hash)

def test_valid_hashes_is_valid():

    words = [generate_pseudo_word() for _ in range(10)]

    for word in words:
        assert verify_hash(encrypt_string(word))

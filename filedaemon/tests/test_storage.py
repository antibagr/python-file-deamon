import os
import pytest

# from tests.environment import (generate_random_url, get_invalid_hashes,
#                                get_test_bytes_object, get_uncloseable_bytes,
#                                remove_test_file, test_file_name)

from storage.manager import StorageMaster, EmptyFileException

@pytest.fixture(scope="session")
def storage_mock(tmpdir_factory):
    fn = tmpdir_factory.mktemp("data")
    return fn

@pytest.fixture(scope='module')
def manager(storage_mock):
    mng = StorageMaster()
    mng.STORAGE = storage_mock
    t = storage_mock / "temp"
    t.mkdir()
    mng.TEMP = t
    return mng


# def test_storage_manager_save(manager):
#
#     assert manager.get('123')[0]

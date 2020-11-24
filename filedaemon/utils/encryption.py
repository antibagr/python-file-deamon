import re

from typing import Optional, Union

from config import HASHING_METHOD, HASH_LENGTH


def encrypt_string(unhashed_string: str, raw: Optional[bool] = False) -> Union[str, bytes]:
    if not isinstance(unhashed_string, str):
        raise ValueError("Please provide string argument")
    hashed = HASHING_METHOD(unhashed_string.encode('utf-8'))
    return hashed.digest() if raw else hashed.hexdigest()


def verify_hash(hash_string: str) -> bool:
    return len(hash_string) == HASH_LENGTH and re.match(r"^[\w\d_-]*$", hash_string)

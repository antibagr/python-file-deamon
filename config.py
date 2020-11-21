import os
import hashlib

# Files related

READING_FILE_BUF_SIZE = 65536  # 64kb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, 'files')
SRC_DIR = os.path.join(BASE_DIR, 'src')
TEMP_DIR = os.path.join(STORAGE_DIR, 'temporary')
HASHING_METHOD = hashlib.sha256
HASH_LENGTH = len(HASHING_METHOD('hashed string'.encode('utf-8')).hexdigest())


# App related

APP_NAME = "Hash Guard"
HOST = 'localhost'
DEBUG = True
MAX_CONTENT_LENGTH = 2 ** 64

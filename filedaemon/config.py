import os
import hashlib

# Files related

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, 'files') # Place where the users' files stored
TEMP_DIR = os.path.join(STORAGE_DIR, 'temporary')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Hash and files related

HASHING_METHOD = hashlib.sha256
HASH_LENGTH = len(HASHING_METHOD('hashed string'.encode('utf-8')).hexdigest())
READING_FILE_BUF_SIZE = 65536  # 64kb


# App related

APP_NAME = "Dr. Hash"
HOST = '0.0.0.0'
DEBUG = True
MAX_CONTENT_LENGTH = 2 ** 64
MAX_CONTENT_LENGTH_VERBOSE = "2 GB"
API_ROOT = 'api'
API_VERSION = 'v1'
API = f'/{API_ROOT}/{API_VERSION}'

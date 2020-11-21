from requests import put, get
put('http://localhost:5000/upload', data={'file': 'Not a file'}).json()
get('http://localhost:5000/download', data={'hash': 'fakehash'}).json()

# Dr.Hash
This is a [Flask](https://flask.palletsprojects.com/en/1.1.x) application which provides a **RESTful API** to your service

# Setup

## Docker

Build the Docker image:

    docker-compose build

Run the docker-compose environment

    docker-compose up -d

This application comes with the unit tests.
To run the tests do

    docker-compose run --rm file_daemon py.test --cov=filedaemon

## Supervisor

As the root user, run the following command to install the Supervisor package

    apt-get install supervisor -y
    service supervisor restart

Edit daemon.conf in a root directory changing **YOUR_PATH_TO_PYTHON** with path to python on your system (you should consider using virtual environment since an application requires dependencies to be installed) and **GIT_REPO_DIRECTORY** to the directory you cloned this repository


Run deamonizing script

    . script.sh

Then you can check that the daemon is running with

    supervisorctl status filedaemon
When you want to stop it, call

    supervisorctl stop filedaemon
Read more about supervisor [at the official page](http://supervisord.org/index.html)


## Standalone

Clone this repository on your local machine

    git clone https://github.com/antibagr/python-file-deamon

Create and activate new virtual environment

    python3 -m venv venv
    . venv/bin/activate

Install dependencies

    cd python-file-deamon
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
Finally, you're able to run server with both

    python filedaemon
 and

    python filedaemon/app.py
Run tests with the following command

    py.test

# Configuration
In `filedaemon` folder you can find `config.py` where you can set desired hasing method, max file size which can accept a server and also various directories.

By default all recevied files stored in `filedaemon/files`

You can change this behavior updating STORAGE_DIR in `config.py`

**Configuration settings works only in standalone and supervisor mode**
Because I didn't have time to set container so it can accept host, port and debug parameters. Stay tuned, though


## API References

 - /api/v1/upload - uploading new file.
	Requires: a file filed in a body request
	Returns: JSON response with filed hashed that contains hash of the stored file
 - /api/v1/download - download a stored file
	 Requires: Hash of previously uploaded file in **hash** field
	 Returns: Stored file if file exists and 404 response if file was not found
 - /api/v1/delete- delete a stored file
	 Requires: Hash of previously uploaded file in **hash** field
	 Returns: 200 response if file was deleted and 404 reponse if file was not found

API always returns a JSON response which contains a **status_code** filed and **message** field. Please notice that not all HTTP method is allowed i.e. /api/v1/download only accept GET method. If a request with invalid method was received, a 405 response will be returned.

If required filed is not provided server wiil anwser with 400 status code.

To see full status code list please refer to docstings of api clases in [api.py](filedaemon/api/api.py)

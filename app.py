import logging
import os

import flask as fl
from flask_restful import Api


from api.api import (UploadRequest, DownloadRequest,
                     DeleteRequest, TeaPotRequest, DefaultRequest)
from api.errors import not_found, request_entity_too_large, default_error_handler
from config import APP_NAME, HOST, DEBUG, MAX_CONTENT_LENGTH, BASE_DIR, STORAGE_DIR, API, API_VERSION, LOG_DIR


class Route:
    """
    Pourly implemented router class
    """

    upload = f'{API}/upload'
    download = f'{API}/download'
    delete = f'{API}/delete'


def create_app() -> fl.app.Flask:
    """
    Entry point for the API
    Creates and returns a flask.app.Flask instance
    """

    app = fl.Flask(__name__)
    api = Api(app)

    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['APP_NAME'] = APP_NAME
    app.config['API_VERSION'] = API_VERSION
    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['UPLOAD_FOLDER'] = STORAGE_DIR

    app.app_context().push()

    api.add_resource(DefaultRequest, '/')
    api.add_resource(UploadRequest, Route.upload)
    api.add_resource(DownloadRequest, Route.download, f'{Route.download}/')
    api.add_resource(DeleteRequest,  Route.delete,  f'{Route.delete}/<string:hash>')
    api.add_resource(TeaPotRequest, '/admin', f'{API}/admin',  f'{API}/admin/<string:anything>')

    app.errorhandler(404)(not_found)
    app.errorhandler(413)(request_entity_too_large)
    app.register_error_handler(Exception, default_error_handler)

    print('everything ok')

    return app


def filelog_constructor(*args, **kw) -> logging.FileHandler:
    """
    Called from logging.yml file to set log file path
    """

    import os

    if not os.path.exists(LOG_DIR):
        os.mkdir(LOG_DIR)

    LOG_FILE = os.path.join(LOG_DIR, 'std_out.log')
    return logging.FileHandler(LOG_FILE)


def setup_logging() -> None:

    import logging.config
    import yaml

    loggingConf = open(os.path.join(BASE_DIR, 'logging.yml'), 'r')
    logging.config.dictConfig(yaml.safe_load(loggingConf))
    loggingConf.close()

    logfile = logging.getLogger('file')
    logconsole = logging.getLogger('console')
    logfile.debug("Debug FILE")
    logconsole.debug("Debug CONSOLE")


if __name__ == '__main__':

    import os
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port: int = args.port

    setup_logging()

    app = create_app()

    app.run(host=HOST, port=port, debug=DEBUG)

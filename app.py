import flask as fl
from flask_restful import Api


from api.api import (UploadRequest, DownloadRequest,
                     DeleteRequest, TeaPotRequest, DefaultRequest)
from api.errors import not_found, request_entity_too_large, default_error_handler
from config import APP_NAME, HOST, DEBUG, MAX_CONTENT_LENGTH, STORAGE_DIR, API, API_VERSION


class Route:

    upload = f'{API}/upload'
    download = f'{API}/download'
    delete = f'{API}/delete'


def create_app() -> fl.app.Flask:

    # for directory in [STORAGE_DIR, TEMP_DIR, SRC_DIR]:
    #     if not os.path.exists(directory):
    #         os.mkdir(directory)

    app = fl.Flask(__name__)
    api = Api(app)

    # max file size is 2 gigabytes
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['APP_NAME'] = APP_NAME
    app.config['API_VERSION'] = API_VERSION
    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['UPLOAD_FOLDER'] = STORAGE_DIR

    app.app_context().push()

    # if USE_DATABASE:
    #     app.config['DATABASE'] = os.path.join(SRC_DIR, 'db.db')
    #     db = Database()
    #     db.init_db()
    #     db.init_app(app)

    api.add_resource(DefaultRequest, '/')
    api.add_resource(UploadRequest, Route.upload)
    api.add_resource(DownloadRequest, Route.download, f'{Route.download}/')
    api.add_resource(DeleteRequest,  Route.delete,  f'{Route.delete}/<string:hash>')
    api.add_resource(TeaPotRequest, '/admin', f'{API}/admin',  f'{API}/admin/<string:anything>')

    app.errorhandler(404)(not_found)
    app.errorhandler(413)(request_entity_too_large)
    app.register_error_handler(Exception, default_error_handler)

    return app



if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app = create_app()

    app.run(host=HOST, port=port, debug=DEBUG)

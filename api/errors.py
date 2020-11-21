import traceback

from werkzeug.exceptions import HTTPException

from .model import Responses


def not_found(error):

    code = 404

    return Responses.Response404


def request_entity_too_large(error):

    code = 413

    # This one doesn't work for some reason
    return Responses.Response413


def default_error_handler(error):

    code = 500

    print(traceback.format_exc())

    if isinstance(error, HTTPException):
        return Responses.Build(message=str(error), status_code=error.code)

    return Responses.Response500

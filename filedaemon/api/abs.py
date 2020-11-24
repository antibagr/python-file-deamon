from flask_restful import Resource, reqparse

from typing import Tuple, Dict, Optional, Any, TypeVar
from typing_extensions import final
from attr import dataclass

from config import APP_NAME, MAX_CONTENT_LENGTH_VERBOSE


StandartResponse = TypeVar(Tuple[Dict, int])


@final
@dataclass(frozen=True, slots=True)
class ResponseBuilder(object):
    """
    Callable object to construct a response.
    """

    def __call__(self, status_code: int = 200, **kw: Any) -> StandartResponse:
        """Constructor for a server responses

        Args:
            status_code (int): . Defaults to 200
            **kw (type): Any parameters that could be jsonified

        Returns:
            StandartResponse: Tuple[Dict, int]
        """
        return {**kw, "status_code": status_code}, status_code


class Responses(object):
    """
    Storage to typed responses of the API.
    """

    NotAllowed = "This method is not allowed. Please use {method} instead"

    Help = {"message": f"Welcome to {APP_NAME}", "status_code": 200}

    Response403 = {"message": "Invalid hash", "status_code": 403}, 403
    Response404 = {"message": "Not found", "status_code": 404}, 404
    Response413 = {"message": f"Max file size is {MAX_CONTENT_LENGTH_VERBOSE}", "status_code": 413}, 413
    Response418 = {"message": "Good try. But I'm a teapot", "status_code": 418}, 418
    Response500 = {"message": "Sorry, there had been internal error", "status_code": 500}, 500

    @staticmethod
    def Build(status_code: int = 200, **kw) -> StandartResponse:
        """Constructor for flask responses

        Args:
            status_code (int): . Defaults to 200
            **kw (type): Any parameters that could be jsonified

        Returns:
            StandartResponse: Tuple[Dict, int]
        """
        return {**kw, "status_code": status_code}, status_code


class BaseRequest(Resource):
    """
    Base Resource class
    Responses with 405 'method not allowed' at every request
    """

    # A verbose string that will be included in message
    # if user will try to access with method
    # not overwritten in child class
    AllowedMethod: str


    def GetParameter(self, parameter_name: str, required: Optional[bool] = False, **kw: Any) -> Any:
        """Lightweight interface to get parameter from json body

        Args:
            parameter_name (str): parameter from json body of the request
            required (Optional[bool]): . Defaults to False.
                We prefer to set parameters as non-required
                to be able to overwrite default missing json-body parameter
                Flask response which missed the status_code filed
            **kw (Any): Any settings to be passed in reqparse.RequestParser().add_argument()

        Returns:
            type: parameter from json body of the request
        """
        parser = reqparse.RequestParser()
        parser.add_argument(parameter_name, **kw, required=required)
        args = parser.parse_args()
        return args[parameter_name]

    def NotAllowed(self) -> StandartResponse:
        return Responses.Build(message=Responses.NotAllowed.format(method=self.AllowedMethod), status_code=405)

    def get(self, **kw) -> StandartResponse:
        return self.NotAllowed()

    def post(self, **kw) -> StandartResponse:
        return self.NotAllowed()

    def put(self, **kw) -> StandartResponse:
        return self.NotAllowed()

    def patch(self, **kw) -> StandartResponse:
        return self.NotAllowed()

    def delete(self, **kw) -> StandartResponse:
        return self.NotAllowed()

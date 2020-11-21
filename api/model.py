from flask_restful import Resource, reqparse

from typing import Tuple, Dict, Optional, Any

from config import APP_NAME


StandartResponse = Tuple[Dict, int]


class Responses:

    NotAllowed = "This method is not allowed. Please use {method} instead"

    Help = {"message": f"Welcome to {APP_NAME}", "status_code": 200}

    Response403 = {"message": "Invalid hash", "status_code": 403}, 403
    Response404 = {"message": "Not found", "status_code": 404}, 404
    Response405 = {"message": "Only POST method is allowed", "status_code": 405}, 405
    Response406 = {"message": "Hash is too long", "status_code": 406}, 406
    Response413 = {"message": "Max file size is 2GB", "status_code": 413}, 413
    Response418 = {"message": "Good try. But I'm a teapot", "status_code": 418}, 418
    Response500 = {"message": "Sorry, there had been internal error", "status_code": 500}, 500

    @staticmethod
    def Build(status_code: int = 200, **kw) -> StandartResponse:
        return {**kw, "status_code": status_code}, status_code


class BaseRequest(Resource):
    """Base Resource class
        Returns 'method not allowed' at every method
    """

    AllowedMethod = ""

    def GetParameter(self, parameter_name: str, required: Optional[bool] = False, **kw: Any) -> Any:
        """Lightweight interface to get parameter from json body

        Args:
            parameter_name (str): parameter from json body of the request
            required (Optional[bool]): . Defaults to False.
                We prefer to set parameters as non-required
                to be able to overwrite default missing json-body parameter
                Flask response which missed the status_code filed
            **kw (Any): Any settings to reqparse.RequestParser().add_argument()

        Returns:
            type: parameter from json body of the request

        Raises:
            ExceptionName: Why the exception is raised.

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

    def copy(self, **kw) -> StandartResponse:
        return self.NotAllowed()

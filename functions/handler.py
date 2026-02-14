
from functions.handler_api import HandlerApi
from functions.handler_sqllite import SQLLiteHandler

class Handler():
    def __init__(self, method):
        self._method = method


    def load(self):
        if self._method == "api":
            return HandlerApi(self)
        elif self._method == "sqlite":
            return SQLLiteHandler(self)
        else:
            raise NotImplementedError(f"Handler method '{self._method}' is not implemented.")
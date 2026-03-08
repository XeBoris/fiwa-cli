
class HandlerApi:
    def __init__(self, handler):
        self.handler = handler

    def get(self, *args, **kwargs):
        return self.handler.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.handler.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.handler.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.handler.delete(*args, **kwargs)
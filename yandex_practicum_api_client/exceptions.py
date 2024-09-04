class YandexPracticumException(Exception):
    def __init__(self, http_status, code=None, message=None, exception=None):
        self.http_status = http_status
        self.code = code
        self.message = message
        self.exception = exception

    def __str__(self):
        if self.message:
            return '{}: http_status: {}; code: {}; message: {}; exception: {};'.format(
                YandexPracticumException.__name__, self.http_status, self.code, self.message, self.exception)
        return f'{YandexPracticumException.__name__}. Unknown error: {self.exception}'

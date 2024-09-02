class YandexPracticumException(Exception):
    def __init__(self, http_status, code=None, message=None):
        self.http_status = http_status
        self.code = code
        self.message = message

    def __str__(self):
        return 'http_status: {}, code: {}, message: {}'.format(
            self.http_status, self.code, self.message)

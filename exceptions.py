class IncorrectEnvironmentVariableValue(Exception):
    """Exception для для ошибок,
      связанных с некорректными значениями переменных окружения"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{IncorrectEnvironmentVariableValue.__name__}: {self.message}"

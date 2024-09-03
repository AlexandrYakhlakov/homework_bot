from requests.sessions import Session
from config import AppConfig
from requests.exceptions import HTTPError, Timeout
from yandex_practicum_api_client.exceptions import YandexPracticumException


class YandexPracticumClient:
    URL = AppConfig.PRACTICUM_API_URL
    TIMEOUT = 15

    def __init__(self):
        self._session = Session()
        self._session.headers['Authorization'] = f'OAuth {AppConfig.PRACTICUM_TOKEN}'

    def _request(self, method, url, params=None, data=None):
        try:
            response = self._session.request(method, url, params, data, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response
        except HTTPError as http_error:
            status_code = http_error.response.status_code
            try:
                response = http_error.response.json()
                raise YandexPracticumException(status_code, response['code'], response['message'])
            except ValueError:
                raise YandexPracticumException(http_status=status_code, message=http_error.response.text)
        except Timeout:
            raise YandexPracticumException(http_status=504, message='Сервис недоступен')

    def homework_statuses(self, from_date=0):
        try:
            params = {'from_date': int(from_date)}
        except ValueError:
            raise ValueError(f'from_date должен быть временем в формате Unix')
        # response = self._session.get(self.URL + 'homework_statuses/',
        #                              headers={'Authorization': f'OAuth {AppConfig.PRACTICUM_TOKEN}'},
        #                              params=params)
        response = self._request('GET', self.URL + 'homework_statuses/', params)
        return response.json()

    def __del__(self):
        self._session.close()


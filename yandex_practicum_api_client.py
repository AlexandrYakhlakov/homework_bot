import os

from requests.sessions import Session
from config import AppConfig


class YandexPracticumClient:
    URL = AppConfig.PRACTICUM_API_URL

    def __init__(self):
        self._session = Session()
        self._session.headers['Authorization'] = f'OAuth {AppConfig.PRACTICUM_TOKEN}'

    # todo: написать обработчик http status_code
    def _request(self, method, url, params=None, data=None):
        self._session.request(method, url, params, data)

    # todo: написать валидатор параметра from_date
    def homework_statuses(self, from_date=None):
        if from_date:
            params = {'from_date': from_date}
        self._request('GET', self.URL + 'homework_statuses/', )

    def __del__(self):
        self._session.close()


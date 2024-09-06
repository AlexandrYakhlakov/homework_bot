import logging
import os
import time
from http import HTTPStatus
from json import JSONDecodeError
from operator import itemgetter

import requests
from requests import RequestException
from telebot import TeleBot

from config import AppConfig

PRACTICUM_TOKEN = AppConfig.PRACTICUM_TOKEN
TELEGRAM_TOKEN = AppConfig.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = AppConfig.TELEGRAM_CHAT_ID

ENV_ERROR_MESSAGE = 'Missing required environment variables: "{env_name}"'
TYPE_ERROR_MESSAGE = ('"{name}" type is not "{expected_type}". '
                      '"{name}" is "{actual_type}"')
KEY_ERROR_MESSAGE = 'Key "{key_name}" not in "{dict_name}"'
REQUEST_DATA_MESSAGE = ('Данные запроса: url: "{url}"; headers: "{headers}"; '
                        'params: "{params}";')
CONNECTION_ERROR_MESSAGE = 'Ошибка соединения: "{exception}"'
UPDATE_STATUS_HOMEWORK_MESSAGE = ('Изменился статус проверки работы "{name}". '
                                  '{verdict}')
UNKNOWN_STATUS_HOMEWORK_MESSAGE = 'Неизвестный статус работы: {name}'
INCORRECT_STATUS_CODE_MESSAGE = 'Некорректный status_code: {status_code}'
RESPONSE_WITH_CODE_MESSAGE = 'Данные ответа: code: "{code}"; error: "{error}"'
INVALID_RESPONSE_BODY_MESSAGE = ('Некорректный тип данных тела ответа, '
                                 'ожидается json. '
                                 'status_code: "{status_code}"; '
                                 'response_body: "{body}"')

RETRY_PERIOD = 10 * 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка значений обязательных переменных окружений приложения."""
    env_names = []
    for env_name in ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
        if globals()[env_name] in (None, ''):
            env_names.append(env_name)
    if len(env_names) != 0:
        logging.critical(ENV_ERROR_MESSAGE.format(env_name=env_names))
        raise EnvironmentError(ENV_ERROR_MESSAGE.format(env_name=env_names))


def send_message(bot, message):
    """Отправка сообщения в чат AppConfig.TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Отправлено сообщение: {message}')
    except Exception as e:
        logging.exception(f'Ошибка отправки сообщения: {e}')


def get_api_answer(timestamp):
    """Запрос и получение ответа от GET /homework_statuses/."""
    params = {'from_date': timestamp}
    request_data_message = REQUEST_DATA_MESSAGE.format(
        url=ENDPOINT, headers=HEADERS, params=params)
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params)
    except (RequestException, ConnectionError) as e:
        raise ConnectionError(CONNECTION_ERROR_MESSAGE.format(
            exception=e) + f'. {request_data_message}')
    try:
        response_json = response.json()
        status_code = response.status_code
        if status_code != HTTPStatus.OK:
            message = (INCORRECT_STATUS_CODE_MESSAGE.format(
                status_code=status_code) + f'. {request_data_message}')
            if 'code' in response_json or 'error' in response_json:
                code = response_json.get('code') or ''
                error = response_json.get('error') or ''
                raise ValueError(f'{message}. '
                                 + RESPONSE_WITH_CODE_MESSAGE.format(
                                     code=code, error=error))
            raise ValueError(f'{message}. Тело ответа: {response_json}')
    except JSONDecodeError:
        raise ValueError(INVALID_RESPONSE_BODY_MESSAGE.format(
            response.status_code, response.text) + f'. {request_data_message}')

    return response_json


def check_response(response):
    """Функция создает и возвращает экземпляр класса HomeworkStatusesDTO."""
    if not isinstance(response, dict):
        raise TypeError(TYPE_ERROR_MESSAGE.format(
            name='response', expected_type='dict', actual_type=type(response)))
    if 'current_date' not in response:
        raise KeyError(KEY_ERROR_MESSAGE.format(
            key_name='current_date',
            dict_name='response'))
    if 'homeworks' not in response:
        raise KeyError(KEY_ERROR_MESSAGE.format(
            key_name='homeworks',
            dict_name='response'))
    if not isinstance(response['homeworks'], list):
        raise TypeError(TYPE_ERROR_MESSAGE.format(
            name='homeworks',
            expected_type='list',
            actual_type=type(response["homeworks"])))
    for homework in response['homeworks']:
        if not isinstance(homework, dict):
            raise TypeError(TYPE_ERROR_MESSAGE.format(
                name='homework',
                expected_type='dict',
                actual_type=type(homework)))


def parse_status(homework):
    """Проверка наличия ключей и значения status."""
    for key in ('homework_name', 'status', 'id'):
        if key not in homework:
            raise KeyError(f'Key "{key}" not found')
    name = homework.get('homework_name')
    status = homework.get('status')

    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    if not verdict:
        raise ValueError(UNKNOWN_STATUS_HOMEWORK_MESSAGE.format(name=status))
    return UPDATE_STATUS_HOMEWORK_MESSAGE.format(name=name, verdict=verdict)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if not response['homeworks']:
                logging.debug('Обновлений по домашним работам не найдено')
                continue
            response['homeworks'].sort(key=itemgetter("id"), reverse=True)
            message = parse_status(response['homeworks'][0])
            timestamp = response['current_date']
            send_message(bot, message)
        except Exception as error:
            logging.exception(error)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    handlers = [logging.StreamHandler()]
    if AppConfig.APP_ENV == 'dev':
        handlers.append(
            logging.FileHandler(os.path.dirname(__file__) + '/.log'))
    logging.basicConfig(
        format=('%(asctime)s - '
                '[%(levelname)s] - '
                '%(funcName)s::%(lineno)d: %(message)s'),
        level=logging.DEBUG,
        handlers=[*handlers]
    )
    main()

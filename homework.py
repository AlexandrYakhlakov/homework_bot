import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from requests import RequestException
from telebot import TeleBot

load_dotenv()

APP_ENV = os.getenv('APP_ENV')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

REQUIRED_ENV_VARS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

ENV_ERROR_MESSAGE = 'Missing required environment variables: "{env_name}"'
TYPE_ERROR_MESSAGE = ('"{name}" type is not "{expected_type}". '
                      '"{name}" is "{actual_type}"')
KEY_ERROR_MESSAGE = 'Key "{key_name}" not in "{dict_name}"'
UNKNOWN_STATUS_HOMEWORK_MESSAGE = 'Неизвестный статус работы: {name}'
UPDATE_STATUS_HOMEWORK_MESSAGE = (
    'Изменился статус проверки работы "{name}". '
    '{verdict}'
)
REQUEST_DATA_MESSAGE = (
    'Данные запроса: url: "{url}"; headers: "{headers}"; '
    'params: "{params}";'
)
CONNECTION_ERROR_MESSAGE = (
    'Ошибка соединения: "{exception}". ' + REQUEST_DATA_MESSAGE
)
RESPONSE_DATA_MESSAGE = 'Данные ответа: code: "{code}"; error: "{error}"'
INCORRECT_STATUS_CODE_MESSAGE = (
    'Некорректный status_code: {status_code}'
    + REQUEST_DATA_MESSAGE
    + RESPONSE_DATA_MESSAGE
)

SENT_TO_TG_MESSAGE = 'Отправлено сообщение: {message}'
NOT_SENT_TO_TG_MESSAGE = (
    'Ошибка:"{exception}"; Сообщение: "{message}"; не отправлено'
)

INVALID_RESPONSE_BODY_MESSAGE = (
    'Некорректный тип данных тела ответа, '
    'ожидается json. '
    'status_code: "{status_code}"; '
    'response_body: "{body}"'
)
NO_HOMEWORK_UPDATES_MESSAGE = 'Обновлений по домашним работам не найдено'
EXCEPTION_MESSAGE = 'Application Error: {error}'

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
    env_names = [
        var for var in REQUIRED_ENV_VARS
        if globals()[var] in (None, '')
    ]
    if env_names:
        logging.critical(ENV_ERROR_MESSAGE.format(env_name=env_names))
        raise EnvironmentError(ENV_ERROR_MESSAGE.format(env_name=env_names))


def send_message(bot, message):
    """Отправка сообщения в чат AppConfig.TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(SENT_TO_TG_MESSAGE.format(message=message))
    except Exception as e:
        logging.exception(NOT_SENT_TO_TG_MESSAGE.format(
            exception=e, message=message))
        return False
    return True


def get_api_answer(timestamp):
    """Запрос и получение ответа от GET /homework_statuses/."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params)
    except RequestException as e:
        raise ConnectionError(
            CONNECTION_ERROR_MESSAGE.format(
                exception=e,
                url=ENDPOINT,
                headers=HEADERS,
                params=params
            )
        )
    response_json = response.json()
    status_code = response.status_code
    if status_code != HTTPStatus.OK:
        error_key_values = {
            key: response_json.get(key, '')
            for key in ('error', 'code')
        }
        raise ValueError(
            INCORRECT_STATUS_CODE_MESSAGE.format(
                status_code=status_code,
                url=ENDPOINT,
                headers=HEADERS,
                params=params,
                **error_key_values
            )
        )
    return response_json


def check_response(response):
    """Функция создает и возвращает экземпляр класса HomeworkStatusesDTO."""
    if not isinstance(response, dict):
        raise TypeError(
            TYPE_ERROR_MESSAGE.format(
                name='response',
                expected_type='dict',
                actual_type=type(response)
            )
        )
    if 'homeworks' not in response:
        raise KeyError(
            KEY_ERROR_MESSAGE.format(
                key_name='homeworks',
                dict_name='response'
            )
        )
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            TYPE_ERROR_MESSAGE.format(
                name='homeworks',
                expected_type='list',
                actual_type=type(homeworks)
            )
        )


def parse_status(homework):
    """Проверка наличия ключей и значения status."""
    for key in ('homework_name', 'status'):
        if key not in homework:
            raise KeyError(
                KEY_ERROR_MESSAGE.format(
                    key_name=key,
                    dict_name='homework'
                )
            )
    name = homework.get('homework_name')
    status = homework.get('status')

    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        raise ValueError(UNKNOWN_STATUS_HOMEWORK_MESSAGE.format(name=status))
    return UPDATE_STATUS_HOMEWORK_MESSAGE.format(name=name, verdict=verdict)


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    last_exception = None
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if not homeworks:
                logging.debug(NO_HOMEWORK_UPDATES_MESSAGE)
                continue
            message = parse_status(homeworks[0])
            if send_message(bot, message):
                timestamp = response.get('current_date', timestamp)
        except Exception as error:
            message = EXCEPTION_MESSAGE.format(error=error)
            logging.exception(message)
            if str(error) != str(last_exception):
                send_message(bot, message)
            last_exception = error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    handlers = [logging.StreamHandler()]
    if APP_ENV != 'prod':
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

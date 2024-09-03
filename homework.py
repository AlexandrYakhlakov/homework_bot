from requests import HTTPError, Timeout, RequestException
from telebot import TeleBot
from config import AppConfig
from exceptions import IncorrectEnvironmentVariableValue
import logging
import time
import requests
from http import HTTPStatus

from yandex_practicum_api_client.exceptions import YandexPracticumException
from dto.homework_statuses_dto import HomeworkStatusesDTO, HomeworkDTO

PRACTICUM_TOKEN = AppConfig.PRACTICUM_TOKEN
TELEGRAM_TOKEN = AppConfig.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = AppConfig.TELEGRAM_CHAT_ID

RETRY_PERIOD = 10
# todo: исправить на 10 минуть при отправке на ревью
# RETRY_PERIOD = 10 * 60
ENDPOINT = AppConfig.PRACTICUM_API_URL + 'homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    config = {key: value for key, value in vars(AppConfig).items() if not key.startswith('__')}
    error_message = ''
    for key, value in config.items():
        if not value:
            error_message += f'Не инициализировано значение переменной окружения {key}\n'
    if error_message:
        raise IncorrectEnvironmentVariableValue(error_message)


def send_message(bot, message):
    ...


def validator_from_date(value):
    """Валидатор для timestamp"""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f'from_date должен быть временем в формате Unix.'
                         f'type from_date: {type(value)}')


def get_api_answer(timestamp):
    """Запрос и получение ответа от GET /homework_statuses/"""
    from_date = validator_from_date(timestamp)
    params = {'from_date': from_date}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise HTTPError
    except HTTPError as http_error:
        status_code = http_error.response.status_code
        try:
            response = http_error.response.json()
            raise YandexPracticumException(status_code, response['code'], response['message'])
        except ValueError:
            raise YandexPracticumException(http_status=status_code, message=http_error.response.text)
    except Timeout:
        raise YandexPracticumException(http_status=504, message='Сервис недоступен')
    except RequestException as e:
        raise YandexPracticumException(http_status=500, exception=e)
    # todo: Написать ревьюеру после сдачи работы. Тесты требуют, чтобы функция возвращала dict.
    #  Какой смысла тогда проверять в check_respons, что респонс это dict?
    #  FAILED tests/test_bot.py::TestHomework::test_get_api_answers - AssertionError:
    #  Проверьте, что функция `get_api_answer` возвращает словарь
    return response.json()


def check_response(response):
    HomeworkStatusesDTO(**response)


def parse_status(homework):
    ...
    # return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    check_tokens()
    bot = TeleBot(token=AppConfig.TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
        finally:
            time.sleep(RETRY_PERIOD)

if __name__ == '__main__':
    main()

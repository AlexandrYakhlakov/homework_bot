import logging
import time
from http import HTTPStatus

import requests
from requests import HTTPError, RequestException, Timeout
from telebot import TeleBot

from config import AppConfig
from dto.homework_statuses_dto import HomeworkStatusesDTO
from exceptions import IncorrectEnvironmentVariableValue
from yandex_practicum_api_client.exceptions import YandexPracticumException

PRACTICUM_TOKEN = AppConfig.PRACTICUM_TOKEN
TELEGRAM_TOKEN = AppConfig.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = AppConfig.TELEGRAM_CHAT_ID

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    level=logging.DEBUG)

RETRY_PERIOD = 10 * 60
ENDPOINT = AppConfig.PRACTICUM_API_URL
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка значений обязательных переменных окружений приложения."""
    if not all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        logging.critical('Отсутствует обязательная переменная окружения')
        raise IncorrectEnvironmentVariableValue(
            'Отсутствует обязательная переменная окружения')


def send_message(bot, message):
    """Отправка сообщения в чат AppConfig.TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Отправлено сообщение: {message}')
    except Exception as e:
        logging.error(f'Ошибка отправки сообщения: {e}')


def get_api_answer(timestamp):
    """Запрос и получение ответа от GET /homework_statuses/."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT + 'homework_statuses/',
                                headers=HEADERS,
                                params=params)
        if response.status_code != HTTPStatus.OK:
            raise HTTPError
    except HTTPError as http_error:
        status_code = response.status_code
        try:
            response = response.json()
            raise YandexPracticumException(http_status=status_code,
                                           code=response['code'],
                                           message=response['message'],
                                           exception=http_error)
        except ValueError:
            raise YandexPracticumException(http_status=status_code,
                                           message=response.text,
                                           exception=http_error)
    except Timeout as e:
        raise YandexPracticumException(http_status=HTTPStatus.GATEWAY_TIMEOUT,
                                       message='Сервис недоступен',
                                       exception=e)
    except RequestException as e:
        raise YandexPracticumException(
            http_status=HTTPStatus.INTERNAL_SERVER_ERROR, exception=e)
    return response.json()


def check_response(response):
    """Функция создает и возвращает экземпляр класса HomeworkStatusesDTO."""
    return HomeworkStatusesDTO(**response)


def parse_status(homework):
    """Валидация сулности и проверка значения status."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError('Key "homework_name" not found')
    status = homework.get('status')
    if not status:
        raise KeyError('Key "status" not found')
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    if not verdict:
        raise ValueError(f'Неизвестный статус работы: {status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    while True:
        try:
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            homeworks_statuses = check_response(response)
            if homeworks_statuses.homeworks:
                for homework in homeworks_statuses.homeworks:
                    message = parse_status(homework.__dict__())
                    send_message(bot, message)
            else:
                logging.debug('Обновлений по домашним работам не найдено')
        except Exception as error:
            logging.error(error, exc_info=True)
            try:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
            except Exception as error:
                logging.error(error, exc_info=True)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

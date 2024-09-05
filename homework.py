import logging
import time
from http import HTTPStatus
from operator import itemgetter
import requests
from requests import HTTPError, RequestException, Timeout
from telebot import TeleBot

from config import AppConfig


PRACTICUM_TOKEN = AppConfig.PRACTICUM_TOKEN
TELEGRAM_TOKEN = AppConfig.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = AppConfig.TELEGRAM_CHAT_ID

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    level=logging.DEBUG)

RETRY_PERIOD = 10 * 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

MESSAGE_FROM_PRAKTIKUM = 'Изменился статус проверки работы "{name}". {verdict}'
ENV_ERROR_MESSAGE = 'Missing required environment variables: {env_name}'


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
    try:
        response = requests.get(ENDPOINT,
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
    if not isinstance(response, dict):
        raise TypeError(f'Validation error: '
                        f'response type is not dict. type(response) is {type(response)}')
    if 'current_date' not in response:
        raise KeyError('Key "current_date" not in response')
    if 'homeworks' not in response:
        raise KeyError('Key "homeworks" not in response')

    if not isinstance(response['homeworks'], list):
        raise TypeError(
            f'Validation error: homeworks type is not list. '
            f' type(homeworks) is {type(response["homeworks"])}')

    for item in response['homeworks']:
        if not isinstance(item, dict):
            raise TypeError('Validation error: homeworks[] item type is not dict. '
                            f'type(homeworks[]) is {type(item)}')


def parse_status(homework):
    """Валидация сулности и проверка значения status."""
    for key in ('homework_name', 'status', 'id'):
        if key not in homework:
            raise KeyError(f'Key "{key}" not found')
    name = homework.get('homework_name')
    status = homework.get('status')

    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    if not verdict:
        raise ValueError(f'Неизвестный статус работы: {status}')
    return MESSAGE_FROM_PRAKTIKUM.format(name=name, verdict=verdict)


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
            try:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
            except Exception as error:
                logging.error(error, exc_info=True)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

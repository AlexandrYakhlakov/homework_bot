from dotenv import load_dotenv
from telebot import TeleBot
from config import AppConfig
from yandex_practicum_api_client.client import YandexPracticumClient
from exceptions import IncorrectEnvironmentVariableValue
import time
from dataclasses import asdict


PRACTICUM_TOKEN = AppConfig.PRACTICUM_TOKEN
TELEGRAM_TOKEN = AppConfig.TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = AppConfig.TELEGRAM_CHAT_ID

RETRY_PERIOD = 10
# todo: исправить на 10 минуть при отправке на ревью
# RETRY_PERIOD = 600
ENDPOINT = AppConfig.PRACTICUM_API_URL
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


def get_api_answer(timestamp):
    session = YandexPracticumClient()
    return session.homework_statuses(timestamp)


def check_response(response):
    ...


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
            print(get_api_answer(timestamp))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
        finally:
            time.sleep(RETRY_PERIOD)

if __name__ == '__main__':
    main()

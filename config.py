import os

from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
    PRACTICUM_API_URL = os.getenv('PRACTICUM_API_URL')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

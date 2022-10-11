import os
import requests
from time import time
import logging
from logging.handlers import RotatingFileHandler

from telegram import Bot
from telegram.ext import MessageHandler

from http import HTTPStatus

from dotenv import load_dotenv


load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YANDEX')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('main.log', maxBytes=50000000, backupCount=1)
formatter = logging.Formatter(
    '%(asctime)s, %(lineno)s, [%(levelname)s], %(message)s'
)
logger.addHandler(handler)
logger.setFormatter(formatter)


def send_message(bot, message):
    """отправка итогового сообщения со всей информацией"""
    pass


def get_api_answer(current_timestamp):
    """Получение ответа от API"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params).json()

    return response[0]


def check_response(response):
    """Проверка запроса к API"""
    if response.status_code == HTTPStatus.OK:
        return response

    logging.error('Сбой в проверке запроса')


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status != 'approved':
        verdict = 'Все ок ты красаффчик, реально'

    verdict = homework.get('reviewer_comment')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    try:
        os.getenv('TOKEN_YANDEX')
        os.getenv('TELEGRAM_TOKEN')
        os.getenv('CHAT_ID')
        return True
    except Exception as error:
        logger.error(error, 'Токены невалидны(какой-то токен потерялся)')
        return False


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_response(response)

            current_timestamp = int(time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error, message)
            time.sleep(RETRY_TIME)
        else:
            


if __name__ == '__main__':
    main()

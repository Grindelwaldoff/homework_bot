import os
import requests
import time
import logging
from logging.handlers import RotatingFileHandler

from telegram import Bot

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

handler = RotatingFileHandler('main.log', maxBytes=50000000, backupCount=1)
formatter = logging.Formatter(
    '%(asctime)s, %(lineno)s, [%(levelname)s], %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
handler.setFormatter(formatter)


def send_message(bot, message):
    """отправка итогового сообщения со всей информацией"""
    text = (f'Имя: {message['homework_name']}'
            f'Статус: {message}'
            f'Комментарий: {message}')

    bot.send_message(TELEGRAM_CHAT_ID, text)


def get_api_answer(current_timestamp):
    """Получение ответа от API"""
    params = {'from_date': current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    return response


def check_response(response):
    """Проверка запроса к API"""
    if response.status_code == HTTPStatus.OK:
        return response.json()

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
    current_timestamp = 0

    while True:
        try:
            response = check_response(get_api_answer(current_timestamp))
            current_timestamp = int(time.time())
            parse_status(response['homeworks'][0])
            message = response['homeworks'][0]
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            logger.error(error, f'Сбой в работе программы: {error}')
            message = f'сбой в программе {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

from http import HTTPStatus
import json
import os
from typing import Dict, List
import requests
import time
import logging

from telegram import Bot

from dotenv import load_dotenv

from exceptions import IncorrectApiResponse


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

logging.basicConfig(level=logging.INFO, filename='main.log', filemode='w')


def check_tokens() -> bool:
    """Проверка всех токенов на валидность."""
    if (TELEGRAM_CHAT_ID is None
            or TELEGRAM_TOKEN is None or PRACTICUM_TOKEN is None):
        logging.critical('Токены не валидны.')
        return False

    return True


def get_api_answer(current_timestamp: int) -> Dict:
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        logging.error('Запрос к API провалился.')
        raise ConnectionRefusedError('Запрос не удался')

    return response.json()


def check_response(response: Dict) -> List[dict]:
    """Проверка запроса к API."""
    if response is None or response['homeworks'] is None:
        raise IncorrectApiResponse('Ответ от API некорректен')

    elif not isinstance(response, Dict):
        raise IncorrectApiResponse('API вернуло не словарь')

    elif 'homeworks' not in response.keys():
        raise IncorrectApiResponse(
            'В ответе API не были получены списки домашних работ'
        )

    elif not isinstance(response['homeworks'], List):
        raise IncorrectApiResponse('Под ключом homeworks не список')

    return response['homeworks']


def parse_status(homework: json) -> str:
    """Получение статуса проверки домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        logging.error('Получен неизвестный статус')
        raise KeyError('Такого статуса не сйществует')
    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: Bot, message: Dict) -> None:
    """Отправка итогового сообщения со всей информацией."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.info('СОобщение успешно отправлено')
    except Exception as error:
        logging.error(error, 'Cообщение не было отправлено.')


def main() -> None:
    """Основная логика работы бота."""
    if check_tokens():
        bot = Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
        status = None

        while True:
            try:
                response = get_api_answer(current_timestamp)
                homework = check_response(response)[0]
                new_status = parse_status(homework)

                if status != new_status:
                    status = new_status
                    message = (
                        f'{status}',
                        f'Статус: {homework.get("status")}',
                        f'Комментарий: {homework.get("reviewer_comment")}'
                    )

                    send_message(bot, message)

                current_timestamp = int(time.time())
                time.sleep(RETRY_TIME)
            except Exception as error:
                logging.error(error, f'Сбой в работе программы: {error}')
                message = f'сбой в программе {error}'
                send_message(bot, message, status)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

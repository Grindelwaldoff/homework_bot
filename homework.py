import os
import sys
import time
import logging
import json
from typing import Dict, List

import requests
from http import HTTPStatus
from telegram import Bot
from dotenv import load_dotenv

from exceptions import (
    JSONEncodeError, IncorrectApiResponse, HTTPError, TelegramError
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_YANDEX')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


# gut
def check_tokens() -> bool:
    """Проверка всех токенов на валидность."""
    check_list = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN
    }
    res = ''

    if not all(check_list.values()):
        for key, value in check_list.items():
            if value is None:
                res += ' ' + key

        raise ValueError(f'Токен/ы {res} не задан/ы.')

    return True


def get_api_answer(current_timestamp: int) -> Dict:
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        raise HTTPError('Запрос не удался')

    return response.json()


def check_response(response: Dict) -> List[dict]:
    """Проверка запроса к API."""
    if response['homeworks'] is None:
        raise KeyError('Ответ от API некорректен')

    if not isinstance(response, Dict):
        raise IncorrectApiResponse('API вернуло не словарь')

    if 'homeworks' not in response.keys():
        raise IncorrectApiResponse(
            'В ответе API не были получены списки домашних работ'
        )

    if not isinstance(response['homeworks'], List):
        raise IncorrectApiResponse(
            'Под ключом homeworks не список'
        )

    return response['homeworks']


def parse_status(homework: json) -> str:
    """Получение статуса проверки домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATES:
        raise KeyError('Такого статуса не существует')

    verdict = HOMEWORK_STATES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def emoji(status: str) -> str:
    """Возвращает для каждого статуса свой смайлик."""
    emojis = {
        'approved': '\U0001F4C8',
        'reviewing': '\U0001F50D',
        'rejected': '\U0001F6A8'
    }
    return emojis[status]


def send_message(bot: Bot, message: Dict) -> None:
    """Отправка итогового сообщения со всей информацией."""
    try:
        # bot.send_message(TELEGRAM_CHAT_ID, text=message)
        print('Все ок')
        logging.info('Сообщение отправлено.')
    except TelegramError:
        raise TelegramError('В ответе содержатся неизвестные символы.')


# gut
def main() -> None:
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.INFO,
        filename='./main.log',
        filemode='w',
        format=(
            'line:%(lineno)s \n'
            'time:%(asctime)s \n'
            'status:%(levelname)s \n'
            'info:%(message)s \n')
    )

    check_tokens()
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
                    f'{status} {emoji(homework["status"])} \n'
                    f'Статус: {homework.get("status")} \U0001F6A9 \n'
                    'Комментарий:'
                    f'{homework.get("reviewer_comment")} \U0001F4DC'
                )

            current_timestamp = int(homework['current_date'])
        except TelegramError as error:
            logging.error(TelegramError, f'Сбой в работе программы: {error}')
            send_message(bot, f'Cбой в программе {error} \U0001F4CC')
            logging.info('Сообщение ошибке успешно отправлено.')
        except ValueError as error:
            logging.critical(error)
            message = error
            sys.exit(1)
        except JSONEncodeError or KeyError or IncorrectApiResponse as error:
            logging.error(error)
            message = error
        else:
            send_message(bot, message)
            logging.info('Все отправилось - прорамма выполнилась')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

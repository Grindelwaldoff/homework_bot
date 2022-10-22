import os
import sys
import time
import logging
import json
from typing import List
from http import HTTPStatus

import requests
from telegram import Bot
from dotenv import load_dotenv

from exceptions import (
    JSONEncodeError, HTTPError,
    TelegramError, RequestException
)


load_dotenv()

BASE_DIR = os.path.dirname(__file__)

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


def check_tokens() -> bool:
    """Проверка всех токенов на валидность."""
    check_list = (PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
    if not all(check_list):
        return False

    return True


def get_api_answer(current_timestamp: int) -> dict:
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except RequestException:
        raise RequestException(
            'Не удалось сделать запрос к API. Сервер не доступен.'
        )

    if not response or response == {}:
        raise TypeError('API сервиса не отвечает.')

    if response.status_code != HTTPStatus.OK:
        raise HTTPError('Сервер сервиса не дал ответа. Error 500.')

    try:
        return response.json()
    except JSONEncodeError:
        raise JSONEncodeError('Ответ от API нельзя перевести в json.')


def check_response(response: dict) -> List[dict]:
    """Проверка запроса к API."""
    if not isinstance(response, dict):
        raise TypeError('API вернуло не словарь.')

    if 'homeworks' not in response.keys():
        raise KeyError(
            'В ответе API не были получены списки домашних работ.'
        )

    if isinstance(response['homeworks'], dict):
        raise TypeError('Дз получено не в виде списка.')

    return response['homeworks']


def parse_status(homework: json) -> str:
    """Получение статуса проверки домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is None:
        raise KeyError('У девочки нет имени... ой, то-есть у дз.')

    if homework_status not in HOMEWORK_STATES:
        raise KeyError(f'{homework_status} - такого статуса нет.')

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


def send_message(bot: Bot, message: dict) -> None:
    """Отправка итогового сообщения со всей информацией."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
    except TelegramError:
        raise TelegramError('В ответе содержатся неизвестные символы.')
    else:
        logging.info('Сообщение отправлено.')


def main() -> None:
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(BASE_DIR, 'main.log'),
        filemode='w',
        format=(
            'line:%(lineno)s \n'
            'time:%(asctime)s \n'
            'status:%(levelname)s \n'
            'info:%(message)s \n')
    )

    if not check_tokens():
        logging.critical('Ошибка с инициализацией Токенов.')
        sys.exit('Ошибка, токены не заданы или заданы, но неправильно.')

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

            current_timestamp = homework['date_updated']
        except TelegramError as error:
            message = f'Cбой в программе {error}'
            logging.error(error, message)
            logging.info('Сообщение об ошибке успешно отправлено.')
        except (
            JSONEncodeError, KeyError, TypeError, HTTPError
        ) as error:
            logging.error(error)
            message = error
        else:
            send_message(bot, message + ' \U0001F4CC')
            logging.info('Все отправилось - прорамма выполнилась')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

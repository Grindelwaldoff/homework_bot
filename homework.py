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
    JSONEncodeError, IncorrectApiResponse,
    HTTPError, TelegramError, RequestException
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

    if not all(check_list.values()):
        return False

    return True


def get_api_answer(current_timestamp: int) -> Dict:
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if not isinstance(response, Dict):
        raise IncorrectApiResponse('API вернуло не словарь.')

    if not response or response == {}:
        raise RequestException('API сервиса не отвечает.')

    if response.status_code != HTTPStatus.OK:
        raise HTTPError('Запрос не удался.')

    try:
        return response.json()
    except JSONEncodeError:
        raise JSONEncodeError('Ответ от API нельзя перевести в json.')


# gut
def check_response(response: Dict) -> List[dict]:
    """Проверка запроса к API."""

    print(response)

    if 'homeworks' not in response.keys():
        raise IncorrectApiResponse(
            'В ответе API не были получены списки домашних работ.'
        )

    # if 'current_date' not in response.keys():
        # raise IncorrectApiResponse(
        #     'В ответе API не было полученно актуальное время.'
        # )

    if response['homeworks'][0] is None:
        raise IncorrectApiResponse('Ответ от API пуст.')

    return response['homeworks']


# gut
def parse_status(homework: json) -> str:
    """Получение статуса проверки домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name == '':
        raise KeyError('У девочки нет имени... ой, то-есть у дз.')

    if homework_status not in HOMEWORK_STATES:
        raise KeyError(f'{homework_status} - такого статуса нет.')

    verdict = HOMEWORK_STATES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# gut
def emoji(status: str) -> str:
    """Возвращает для каждого статуса свой смайлик."""
    emojis = {
        'approved': '\U0001F4C8',
        'reviewing': '\U0001F50D',
        'rejected': '\U0001F6A8'
    }
    return emojis[status]


# gut
def send_message(bot: Bot, message: Dict) -> None:
    """Отправка итогового сообщения со всей информацией."""
    try:
        # bot.send_message(TELEGRAM_CHAT_ID, text=message)
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

    if not check_tokens():
        raise ValueError('Ошибка инициализации Токенов.')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(0)
    status = None

    while True:
        try:
            try:
                response = get_api_answer(current_timestamp)
            except RequestException as error:
                logging.critical(error, __doc__)
                message = error

            homework = check_response(response)
            new_status = parse_status(homework[0])

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
            logging.error(error, f'Сбой в работе программы: {error}')
            send_message(bot, f'Cбой в программе {error} \U0001F4CC')
            logging.info('Сообщение ошибке успешно отправлено.')
        except ValueError as error:
            logging.critical(error)
            message = error
            sys.exit(1)
        except (
            JSONEncodeError or KeyError or IncorrectApiResponse or HTTPError
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

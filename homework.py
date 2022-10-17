import sys

from http import HTTPStatus
import json
import os
from typing import Dict, List
from urllib.error import HTTPError
import requests
import time
import logging

from telegram import Bot, TelegramError

from dotenv import load_dotenv

from exceptions import IncorrectApiResponse


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


def check_tokens() -> bool:
    """Проверка всех токенов на валидность."""
    if (
        globals()['PRACTICUM_TOKEN'] is None
        or globals()['TELEGRAM_CHAT_ID'] is None
        or globals()['TELEGRAM_TOKEN'] is None
    ):
        return False

    return True


def get_api_answer(current_timestamp: int) -> Dict:
    """Получение ответа от API."""
    params = {'from_date': current_timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        raise ConnectionRefusedError('Запрос не удался')

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
        raise IncorrectApiResponse('Под ключом homeworks не список')

    return response['homeworks']


def parse_status(homework: json) -> str:
    """Получение статуса проверки домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in HOMEWORK_STATES:
        raise KeyError('Такого статуса не сйществует')

    verdict = HOMEWORK_STATES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: Bot, message: Dict) -> None:
    """Отправка итогового сообщения со всей информацией."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
    except TelegramError:
        raise TelegramError('В ответе содержатся неизвестные символы.')


def main() -> None:
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.INFO,
        filename='./main.log',
        filemode='w'
    )

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(0)
    status = None

    while True:
        try:
            if not check_tokens():
                raise ValueError('Какой-то из токенов потерялся')
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

            current_timestamp = int(0)
        except TelegramError as error:
            logging.error(TelegramError, f'Сбой в работе программы: {error}')
            send_message(bot, f'Cбой в программе {error}')
            logging.info('Сообщение ошибке успешно отправлено.')
        except KeyError:
            logging.error(KeyError)
        except ValueError:
            logging.critical(ValueError)
            sys.exit()
        except HTTPError or ConnectionRefusedError as error:
            logging.error(error)
        except requests.JSONDecodeError:
            logging.error(requests.JSONDecodeError,
                          'Не удалось привести вывод API к формату JSON')
        else:
            logging.info('Все отправилось - прорамма выполнилась')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

from requests import RequestException
from telegram import TelegramError


class JSONEncodeError(RequestException):
    """Ошибка в выводе результата в JSON формат."""

    pass


class IncorrectApiResponse(Exception):
    """Ошибка в выводе резльтата от API."""

    pass


class HTTPError(RequestException):
    """Ошибка - не удалось получить ответ от API."""

    pass


class TelegramError(TelegramError):
    """Ошибка при взаимодействии с API телеграма."""

    pass

from requests.exceptions import RequestException
from telegram import TelegramError


class JSONEncodeError(RequestException):
    """Ошибка в выводе результата в JSON формат."""

    pass


class HTTPError(RequestException):
    """Ошибка - не удалось получить ответ от API."""

    pass


class TelegramError(TelegramError):
    """Ошибка при взаимодействии с API телеграма."""

    pass


class RequestException(ConnectionAbortedError):
    """Ошибка вызова response."""

    pass

class CheckResponseLogError(KeyError):
    """Параметр current_date не был получен в ответе от API."""

    pass


class MyTelegramError(Exception):
    """Ошибка при взаимодействии с API телеграма."""

    pass


class RequestException(ConnectionError):
    """Ошибка вызова response."""

    pass

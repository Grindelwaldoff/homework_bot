class CheckResponseLogError(KeyError):
    """Параметр current_date не был получен в ответе от API."""

    pass


class SendMessageError(Exception):
    """Ошибка при взаимодействии с API телеграма."""

    pass


class APIError(ConnectionError):
    """Ошибка вызова response."""

    pass

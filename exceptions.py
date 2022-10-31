class LogError(Exception):
    """Ошибка для логирования."""

    pass


class CheckResponseLogError(LogError):
    """Параметр current_date не был получен в ответе от API."""

    pass


class SendMessageError(LogError):
    """Ошибка при взаимодействии с API телеграма."""

    pass


class APIError(ConnectionError):
    """Ошибка вызова response."""

    pass

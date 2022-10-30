class CheckResponseLogError(KeyError):
    """Параметр current_date не был получен в ответе от API."""

    pass


class CustomTelegramError(Exception):
    """Ошибка при взаимодействии с API телеграма."""

    pass


class CustomRequestException(ConnectionError):
    """Ошибка вызова response."""

    pass

import logging


def IncorrectApiResponse(message):
    """Ошибка вызываемая при сбое в запросе к  API."""
    logging.error(message)

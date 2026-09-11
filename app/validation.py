"""проверка входящих данных"""

BAD_REQUEST = 400
NOT_FOUND = 404
SERVER_ERROR = 500


class ApiError(Exception):
    """ошибка обработки запроса с кодом ответа"""

    def __init__(self, status: int, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason

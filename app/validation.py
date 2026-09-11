"""проверка входящих данных"""

import typing as tp

BAD_REQUEST = 400
NOT_FOUND = 404
SERVER_ERROR = 500


class ApiError(Exception):
    """ошибка обработки запроса с кодом ответа"""

    def __init__(self, status: int, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason


def payload(body: tp.Any, wrapper: str) -> tp.Dict[str, tp.Any]:
    """тело запроса без внешней обёртки"""
    if not isinstance(body, dict):
        raise ApiError(BAD_REQUEST, "Request body should be a json object")
    inner = body.get(wrapper, body)
    if not isinstance(inner, dict):
        raise ApiError(BAD_REQUEST, f"Field '{wrapper}' should be a json object")
    return inner

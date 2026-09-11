"""проверка входящих данных"""

import typing as tp
import uuid

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


def string_field(
    data: tp.Dict[str, tp.Any],
    field: str,
    limit: int,
    required: bool,
) -> tp.Optional[str]:
    """строковое поле с ограничением длины"""
    if field not in data:
        if required:
            raise ApiError(BAD_REQUEST, f"Field '{field}' is required")
        return None
    value = data[field]
    if not isinstance(value, str) or not value.strip():
        raise ApiError(BAD_REQUEST, f"Field '{field}' is required")
    if len(value) > limit:
        raise ApiError(BAD_REQUEST, f"Field '{field}' should be shorter than {limit}")
    return value.strip()


def uuid_field(data: tp.Dict[str, tp.Any], field: str, required: bool) -> tp.Optional[str]:
    """поле с идентификатором в формате uuid"""
    if field not in data:
        if required:
            raise ApiError(BAD_REQUEST, f"Field '{field}' is required")
        return None
    value = data[field]
    if not isinstance(value, str) or not value.strip():
        raise ApiError(BAD_REQUEST, f"Field '{field}' is required")
    try:
        return str(uuid.UUID(value))
    except ValueError as error:
        raise ApiError(BAD_REQUEST, f"Field '{field}' should be a valid uuid") from error


def valid_uuid(value: str) -> bool:
    """проверить, что строка это uuid"""
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True

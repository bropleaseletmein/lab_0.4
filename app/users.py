"""эндпоинты пользователей"""

import typing as tp

import flask

from app import validation
from app.models import User

blueprint = flask.Blueprint("users", __name__, url_prefix="/api/users")


def find_user(user_id: str) -> User:
    """живой пользователь или ошибка 404"""
    if not validation.valid_uuid(user_id):
        raise validation.ApiError(validation.NOT_FOUND, f"User '{user_id}' is not found")
    user = User.active_by_id(user_id)
    if user is None:
        raise validation.ApiError(validation.NOT_FOUND, f"User '{user_id}' is not found")
    return user


def read_payload() -> tp.Dict[str, tp.Any]:
    """тело запроса с пользователем"""
    return validation.payload(flask.request.get_json(silent=True), "user")


@blueprint.get("")
def list_users() -> flask.Response:
    """список живых пользователей"""
    users = User.active_list(User.active().order_by(User.created_at))
    return flask.jsonify({"list": [user.to_dict() for user in users]})


@blueprint.get("/<user_id>")
def get_user(user_id: str) -> flask.Response:
    """пользователь по идентификатору"""
    return flask.jsonify({"user": find_user(user_id).to_dict()})

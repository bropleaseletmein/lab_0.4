"""эндпоинты пользователей"""

import typing as tp

import flask
import peewee

from app import validation
from app.models import FIO_LIMIT, LOGIN_LIMIT, Note, User

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


@blueprint.post("")
def create_user() -> flask.Response:
    """создать пользователя"""
    data = read_payload()
    login = validation.string_field(data, "login", LOGIN_LIMIT, required=True)
    fio = validation.string_field(data, "fio", FIO_LIMIT, required=True)
    if User.active().where(User.login == login).exists():
        reason = f"Field 'login' should be unique, '{login}' is taken"
        raise validation.ApiError(validation.BAD_REQUEST, reason)
    try:
        user = User.create(login=login, fio=fio)
    except peewee.IntegrityError as error:
        raise validation.ApiError(validation.SERVER_ERROR, str(error)) from error
    return flask.jsonify({"user": user.to_dict()})


@blueprint.patch("/<user_id>")
def update_user(user_id: str) -> flask.Response:
    """изменить пользователя"""
    user = find_user(user_id)
    data = read_payload()
    login = validation.string_field(data, "login", LOGIN_LIMIT, required=False)
    fio = validation.string_field(data, "fio", FIO_LIMIT, required=False)
    if login is not None:
        taken = User.active().where(User.login == login, User.id != user.id)
        if taken.exists():
            reason = f"Field 'login' should be unique, '{login}' is taken"
            raise validation.ApiError(validation.BAD_REQUEST, reason)
        user.login = login
    if fio is not None:
        user.fio = fio
    user.save()
    return flask.jsonify({"user": user.to_dict()})


@blueprint.delete("/<user_id>")
def delete_user(user_id: str) -> tp.Tuple[flask.Response, int]:
    """пометить пользователя удалённым вместе с его заметками"""
    user = find_user(user_id)
    for note in Note.active_list(Note.active().where(Note.user == user)):
        note.soft_delete()
    user.soft_delete()
    return flask.jsonify({"user": user.to_dict()}), 202

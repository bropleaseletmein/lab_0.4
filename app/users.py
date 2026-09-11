"""эндпоинты пользователей"""

import typing as tp

import flask

from app import validation
from app.models import User

blueprint = flask.Blueprint("users", __name__, url_prefix="/api/users")


def read_payload() -> tp.Dict[str, tp.Any]:
    """тело запроса с пользователем"""
    return validation.payload(flask.request.get_json(silent=True), "user")


@blueprint.get("")
def list_users() -> flask.Response:
    """список живых пользователей"""
    users = User.active_list(User.active().order_by(User.created_at))
    return flask.jsonify({"list": [user.to_dict() for user in users]})

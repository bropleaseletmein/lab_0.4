"""эндпоинты заметок"""

import typing as tp

import flask

from app import validation
from app.models import Note

blueprint = flask.Blueprint("notes", __name__, url_prefix="/api/notes")


def read_payload() -> tp.Dict[str, tp.Any]:
    """тело запроса с заметкой"""
    return validation.payload(flask.request.get_json(silent=True), "note")


@blueprint.get("")
def list_notes() -> flask.Response:
    """список живых заметок с фильтром по автору"""
    notes = Note.active()
    user_id = flask.request.args.get("user_id")
    if user_id is not None:
        if not validation.valid_uuid(user_id):
            reason = "Field 'user_id' should be a valid uuid"
            raise validation.ApiError(validation.BAD_REQUEST, reason)
        notes = notes.where(Note.user == user_id)
    found = Note.active_list(notes.order_by(Note.created_at))
    return flask.jsonify({"list": [note.to_dict() for note in found]})

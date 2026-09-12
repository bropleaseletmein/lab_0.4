"""эндпоинты заметок"""

import typing as tp

import flask

from app import validation
from app.models import Note

blueprint = flask.Blueprint("notes", __name__, url_prefix="/api/notes")


def find_note(note_id: str) -> Note:
    """живая заметка или ошибка 404"""
    if not validation.valid_uuid(note_id):
        raise validation.ApiError(validation.NOT_FOUND, f"Note '{note_id}' is not found")
    note = Note.active_by_id(note_id)
    if note is None:
        raise validation.ApiError(validation.NOT_FOUND, f"Note '{note_id}' is not found")
    return note


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


@blueprint.get("/<note_id>")
def get_note(note_id: str) -> flask.Response:
    """заметка по идентификатору"""
    return flask.jsonify({"note": find_note(note_id).to_dict()})

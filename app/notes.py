"""эндпоинты заметок"""

import typing as tp

import flask

from app import validation
from app.models import BODY_LIMIT, TITLE_LIMIT, Note, User

blueprint = flask.Blueprint("notes", __name__, url_prefix="/api/notes")


def find_note(note_id: str) -> Note:
    """живая заметка или ошибка 404"""
    if not validation.valid_uuid(note_id):
        raise validation.ApiError(validation.NOT_FOUND, f"Note '{note_id}' is not found")
    note = Note.active_by_id(note_id)
    if note is None:
        raise validation.ApiError(validation.NOT_FOUND, f"Note '{note_id}' is not found")
    return note


def find_owner(user_id: str) -> User:
    """живой автор заметки или ошибка валидации"""
    user = User.active_by_id(user_id)
    if user is None:
        reason = f"Field 'user_id' references unknown user '{user_id}'"
        raise validation.ApiError(validation.BAD_REQUEST, reason)
    return user


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


@blueprint.post("")
def create_note() -> flask.Response:
    """создать заметку"""
    data = read_payload()
    user_id = validation.uuid_field(data, "user_id", required=True)
    title = validation.string_field(data, "title", TITLE_LIMIT, required=True)
    body = validation.string_field(data, "body", BODY_LIMIT, required=True)
    note = Note.create(user=find_owner(str(user_id)), title=title, body=body)
    return flask.jsonify({"note": note.to_dict()})


@blueprint.patch("/<note_id>")
def update_note(note_id: str) -> flask.Response:
    """изменить заметку"""
    note = find_note(note_id)
    data = read_payload()
    user_id = validation.uuid_field(data, "user_id", required=False)
    title = validation.string_field(data, "title", TITLE_LIMIT, required=False)
    body = validation.string_field(data, "body", BODY_LIMIT, required=False)
    if user_id is not None:
        note.user = find_owner(user_id)
    if title is not None:
        note.title = title
    if body is not None:
        note.body = body
    note.save()
    return flask.jsonify({"note": note.to_dict()})


@blueprint.delete("/<note_id>")
def delete_note(note_id: str) -> tp.Tuple[flask.Response, int]:
    """пометить заметку удалённой"""
    note = find_note(note_id)
    note.soft_delete()
    return flask.jsonify({"note": note.to_dict()}), 202

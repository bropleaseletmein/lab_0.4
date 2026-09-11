"""сборка приложения flask"""

import pathlib
import typing as tp

import flask
import werkzeug.exceptions

from app import notes, users
from app.database import connect, database
from app.validation import NOT_FOUND, SERVER_ERROR, ApiError


def error_body(status: int, reason: str) -> tp.Tuple[flask.Response, int]:
    """ответ с описанием ошибки"""
    return flask.jsonify({"status": status, "reason": reason}), status


def register_handlers(app: flask.Flask) -> None:
    """обработчики ошибок в формате задания"""

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError) -> tp.Tuple[flask.Response, int]:
        """ошибка с известным кодом"""
        return error_body(error.status, error.reason)

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def handle_missing_route(error: werkzeug.exceptions.NotFound) -> tp.Tuple[flask.Response, int]:
        """неизвестный маршрут"""
        return error_body(NOT_FOUND, error.description)

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception) -> tp.Tuple[flask.Response, int]:
        """любая другая ошибка"""
        return error_body(SERVER_ERROR, str(error))


def register_connection(app: flask.Flask) -> None:
    """соединение с базой на время запроса"""

    @app.before_request
    def open_connection() -> None:
        """открыть соединение"""
        database.connect(reuse_if_open=True)

    @app.teardown_request
    def close_connection(error: tp.Optional[BaseException] = None) -> None:
        """закрыть соединение"""
        del error
        if not database.is_closed():
            database.close()


def create_app(database_path: tp.Optional[tp.Union[str, pathlib.Path]] = None) -> flask.Flask:
    """создать приложение с подключённой базой"""
    app = flask.Flask(__name__)
    connect(database_path)
    app.register_blueprint(users.blueprint)
    app.register_blueprint(notes.blueprint)
    register_connection(app)
    register_handlers(app)
    return app

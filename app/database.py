"""подключение к базе данных"""

import pathlib
import typing as tp

import peewee

DATABASE_PATH = pathlib.Path(__file__).resolve().parent.parent / "notes.db"

database = peewee.SqliteDatabase(None)


def connect(path: tp.Optional[tp.Union[str, pathlib.Path]] = None) -> peewee.SqliteDatabase:
    """открыть соединение, переключив базу при смене пути"""
    target = str(path or DATABASE_PATH)
    if database.database != target:
        if not database.is_closed():
            database.close()
        database.init(target, pragmas={"foreign_keys": 1})
    database.connect(reuse_if_open=True)
    return database


class BaseModel(peewee.Model):
    """общие настройки моделей"""

    class Meta:
        """все таблицы лежат в одной базе"""

        database = database

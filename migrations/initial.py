"""создание таблиц пользователей и заметок"""

import peewee

from app.models import Note, User

NAME = "0001_initial"


def apply(database: peewee.Database) -> None:
    """создать таблицы вместе с индексами"""
    database.create_tables([User, Note])

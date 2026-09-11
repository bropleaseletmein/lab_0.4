"""накатывание миграций на базу"""

import datetime
import pathlib
import typing as tp

import peewee

from app.database import BaseModel, connect, database
from migrations import initial

MIGRATIONS = [initial]


class MigrationHistory(BaseModel):
    """журнал применённых миграций"""

    name = peewee.CharField(max_length=100, unique=True)
    applied_at = peewee.DateTimeField(default=datetime.datetime.now)


def run(path: tp.Optional[tp.Union[str, pathlib.Path]] = None) -> tp.List[str]:
    """применить ещё не накатанные миграции"""
    connect(path)
    database.create_tables([MigrationHistory])
    applied = {row.name for row in MigrationHistory.select()}
    fresh = []
    for migration in MIGRATIONS:
        if migration.NAME in applied:
            continue
        migration.apply(database)
        MigrationHistory.create(name=migration.NAME)
        fresh.append(migration.NAME)
    return fresh


def main() -> None:
    """накатить миграции и сообщить результат"""
    fresh = run()
    if fresh:
        for name in fresh:
            print(f"применена миграция {name}")
    else:
        print("новых миграций нет")


if __name__ == "__main__":
    main()

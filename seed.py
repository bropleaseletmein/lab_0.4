"""наполнение базы начальными данными"""

import pathlib
import typing as tp

from app.database import connect
from app.models import Note, User

USERS = [
    ("voronin", "Воронин Владимир Никитич"),
    ("popov", "Попов Кирилл Артёмович"),
    ("kruglova", "Круглова Александра Ивановна"),
    ("polyakov", "Поляков Макар Дмитриевич"),
]

NOTES = {
    "voronin": [
        ("Список покупок", "хлеб, молоко, гречка, яблоки"),
        ("Планы на неделю", "закрыть отчёт, сходить в спортзал, позвонить родителям"),
        ("Пароли", "поменять пароль от почты до пятницы"),
        ("Идея", "сделать бота, который напоминает про счётчики"),
    ],
    "popov": [
        ("Тренировка", "понедельник спина, среда ноги, пятница грудь"),
        ("Книги", "дочитать про архитектуру, начать про алгоритмы"),
        ("Ремонт", "замерить кухню, выбрать плитку"),
    ],
    "kruglova": [
        ("Рецепт", "тесто два часа в холодильнике, духовка сто восемьдесят"),
        ("Отпуск", "билеты на июнь, гостиница у моря, страховка"),
        ("Учёба", "сдать лабораторную по базам данных"),
        ("Подарки", "родителям на годовщину, брату на день рождения"),
        ("Долги", "вернуть книгу в библиотеку"),
    ],
    "polyakov": [
        ("Работа", "созвон в десять, ревью до обеда, деплой вечером"),
        ("Машина", "замена масла на следующей неделе"),
        ("Музыка", "разобрать вторую часть сонаты"),
        ("Заметка", "проверить счётчики до двадцать пятого"),
    ],
}


def fill() -> tp.Tuple[int, int]:
    """создать пользователей с заметками"""
    created_users = 0
    created_notes = 0
    for login, fio in USERS:
        if User.active().where(User.login == login).exists():
            continue
        user = User.create(login=login, fio=fio)
        created_users += 1
        for title, body in NOTES[login]:
            Note.create(user=user, title=title, body=body)
            created_notes += 1
    return created_users, created_notes


def main(path: tp.Optional[tp.Union[str, pathlib.Path]] = None) -> None:
    """наполнить базу и сообщить результат"""
    connect(path)
    users_count, notes_count = fill()
    print(f"добавлено пользователей: {users_count}")
    print(f"добавлено заметок: {notes_count}")


if __name__ == "__main__":
    main()

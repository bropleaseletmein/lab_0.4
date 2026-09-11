"""модели пользователей и заметок"""

import datetime
import typing as tp
import uuid

import peewee

from app.database import BaseModel

LOGIN_LIMIT = 50
FIO_LIMIT = 100
TITLE_LIMIT = 100
BODY_LIMIT = 5000

ModelT = tp.TypeVar("ModelT", bound="SoftDeleteModel")


def as_iso(value: tp.Optional[datetime.datetime]) -> tp.Optional[str]:
    """время в формате iso или none"""
    return value.isoformat() if value else None


class SoftDeleteModel(BaseModel):
    """запись, которая удаляется пометкой"""

    id = peewee.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)
    is_deleted = peewee.BooleanField(default=False)
    deleted_at = peewee.DateTimeField(null=True, default=None)

    @classmethod
    def active(cls) -> "peewee.ModelSelect[tp.Any]":
        """записи без пометки удаления"""
        return cls.select().where(~cls.is_deleted)

    @classmethod
    def active_list(
        cls: tp.Type[ModelT],
        query: tp.Optional["peewee.ModelSelect[tp.Any]"] = None,
    ) -> tp.List[ModelT]:
        """живые записи списком"""
        return tp.cast(tp.List[ModelT], list(cls.active() if query is None else query))

    @classmethod
    def active_by_id(cls: tp.Type[ModelT], record_id: str) -> tp.Optional[ModelT]:
        """живая запись по идентификатору"""
        return tp.cast(tp.Optional[ModelT], cls.active().where(cls.id == record_id).first())

    def soft_delete(self) -> None:
        """пометить запись удалённой"""
        self.is_deleted = True
        self.deleted_at = datetime.datetime.now()
        self.save()


class User(SoftDeleteModel):
    """пользователь сервиса"""

    login = peewee.CharField(max_length=LOGIN_LIMIT, unique=True)
    fio = peewee.CharField(max_length=FIO_LIMIT)

    def to_dict(self) -> tp.Dict[str, tp.Any]:
        """представление пользователя для json"""
        return {
            "id": str(self.id),
            "login": self.login,
            "fio": self.fio,
            "created_at": as_iso(self.created_at),
            "is_deleted": self.is_deleted,
            "deleted_at": as_iso(self.deleted_at),
        }


class Note(SoftDeleteModel):
    """заметка пользователя"""

    user = peewee.ForeignKeyField(User, backref="notes", column_name="user_id", index=True)
    title = peewee.CharField(max_length=TITLE_LIMIT)
    body = peewee.TextField()

    @property
    def owner_id(self) -> str:
        """идентификатор автора без обращения к таблице пользователей"""
        return str(getattr(self, "user_id"))

    def to_dict(self) -> tp.Dict[str, tp.Any]:
        """представление заметки для json"""
        return {
            "id": str(self.id),
            "user_id": self.owner_id,
            "title": self.title,
            "body": self.body,
            "created_at": as_iso(self.created_at),
            "is_deleted": self.is_deleted,
            "deleted_at": as_iso(self.deleted_at),
        }

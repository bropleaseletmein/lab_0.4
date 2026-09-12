"""тесты миграций, моделей и наполнения"""

import pathlib
import shutil
import tempfile
import unittest

import seed
from app.database import database
from app.models import Note, User
from migrate import MigrationHistory, run
from tests.base import ApiTestCase


class MigrationTestCase(unittest.TestCase):
    """накатывание миграций"""

    def setUp(self) -> None:
        """чистая база во временном каталоге"""
        self.folder = tempfile.mkdtemp()
        self.path = pathlib.Path(self.folder) / "test.db"

    def tearDown(self) -> None:
        """закрыть соединение и убрать файлы"""
        if not database.is_closed():
            database.close()
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_creates_database_file(self) -> None:
        """файл базы появляется в дереве"""
        run(self.path)
        self.assertTrue(self.path.exists())

    def test_applies_initial(self) -> None:
        """первая миграция накатывается"""
        self.assertEqual(run(self.path), ["0001_initial"])

    def test_is_idempotent(self) -> None:
        """повторный запуск ничего не накатывает"""
        run(self.path)
        self.assertEqual(run(self.path), [])

    def test_writes_history(self) -> None:
        """применённая миграция попадает в журнал"""
        run(self.path)
        names = [row.name for row in MigrationHistory.select()]
        self.assertEqual(names, ["0001_initial"])

    def test_creates_tables(self) -> None:
        """таблицы пользователей и заметок созданы"""
        run(self.path)
        self.assertTrue(User.table_exists())
        self.assertTrue(Note.table_exists())

    def test_creates_index_on_foreign_key(self) -> None:
        """на внешнем ключе заметки есть индекс"""
        run(self.path)
        rows = database.execute_sql("PRAGMA index_list('note')").fetchall()
        self.assertIn("note_user_id", [row[1] for row in rows])

    def test_primary_keys_are_uuid(self) -> None:
        """первичные ключи хранятся как текст"""
        run(self.path)
        columns = database.execute_sql("PRAGMA table_info('user')").fetchall()
        types = {row[1]: row[2] for row in columns}
        self.assertEqual(types["id"], "TEXT")


class SeedTestCase(ApiTestCase):
    """наполнение базы"""

    def test_fills_users_and_notes(self) -> None:
        """создаются пользователи с заметками"""
        users_count, notes_count = seed.fill()
        self.assertEqual(users_count, 4)
        self.assertEqual(notes_count, 16)

    def test_is_idempotent(self) -> None:
        """повторное наполнение ничего не добавляет"""
        seed.fill()
        self.assertEqual(seed.fill(), (0, 0))

    def test_every_user_has_notes(self) -> None:
        """у каждого пользователя есть от трёх до пяти заметок"""
        seed.fill()
        for user in User.active_list():
            with self.subTest(login=user.login):
                count = Note.active().where(Note.user == user).count()
                self.assertGreaterEqual(count, 3)
                self.assertLessEqual(count, 5)

    def test_visible_through_api(self) -> None:
        """наполненные данные отдаются через api"""
        seed.fill()
        self.assertEqual(len(self.client.get("/api/users").get_json()["list"]), 4)
        self.assertEqual(len(self.client.get("/api/notes").get_json()["list"]), 16)


class SoftDeleteTestCase(ApiTestCase):
    """мягкое удаление на уровне моделей"""

    def test_record_stays_in_table(self) -> None:
        """после удаления строка остаётся в таблице"""
        user = User.create(login="ivan", fio="Иванов Иван")
        user.soft_delete()
        self.assertEqual(len(list(User.select())), 1)
        self.assertEqual(User.active().count(), 0)

    def test_sets_deleted_at(self) -> None:
        """проставляется отметка времени удаления"""
        user = User.create(login="ivan", fio="Иванов Иван")
        self.assertIsNone(user.deleted_at)
        user.soft_delete()
        self.assertIsNotNone(user.deleted_at)

    def test_active_by_id_skips_deleted(self) -> None:
        """поиск живой записи не находит удалённую"""
        user = User.create(login="ivan", fio="Иванов Иван")
        self.assertIsNotNone(User.active_by_id(str(user.id)))
        user.soft_delete()
        self.assertIsNone(User.active_by_id(str(user.id)))

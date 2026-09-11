"""тесты миграций, моделей и наполнения"""

import pathlib
import shutil
import tempfile
import unittest

from app.database import database
from app.models import Note, User
from migrate import MigrationHistory, run


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

"""общая основа тестов"""

import pathlib
import shutil
import tempfile
import typing as tp
import unittest

from app.database import database
from app.factory import create_app
from migrate import run


class ApiTestCase(unittest.TestCase):
    """тест с отдельной базой на каждый запуск"""

    def setUp(self) -> None:
        """поднять чистую базу и тестовый клиент"""
        self.folder = tempfile.mkdtemp()
        self.path = pathlib.Path(self.folder) / "test.db"
        run(self.path)
        self.app = create_app(self.path)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        """закрыть соединение и убрать временные файлы"""
        if not database.is_closed():
            database.close()
        shutil.rmtree(self.folder, ignore_errors=True)

    def make_user(
        self,
        login: str = "ivan",
        fio: str = "Иванов Иван Иванович",
    ) -> tp.Dict[str, tp.Any]:
        """создать пользователя через api"""
        response = self.client.post("/api/users", json={"user": {"login": login, "fio": fio}})
        self.assertEqual(response.status_code, 200)
        return response.get_json()["user"]

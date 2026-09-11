"""тесты эндпоинтов пользователей"""

from tests.base import ApiTestCase

MISSING_ID = "11111111-1111-1111-1111-111111111111"


class ListUsersTestCase(ApiTestCase):
    """список пользователей"""

    def test_empty_list(self) -> None:
        """на чистой базе список пуст"""
        response = self.client.get("/api/users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"list": []})

    def test_list_contains_created(self) -> None:
        """созданный пользователь попадает в список"""
        user = self.make_user()
        response = self.client.get("/api/users")
        logins = [item["login"] for item in response.get_json()["list"]]
        self.assertEqual(logins, [user["login"]])

    def test_deleted_user_is_hidden(self) -> None:
        """удалённый пользователь в списке не показывается"""
        user = self.make_user()
        self.client.delete(f"/api/users/{user['id']}")
        self.assertEqual(self.client.get("/api/users").get_json(), {"list": []})


class GetUserTestCase(ApiTestCase):
    """получение пользователя"""

    def test_found(self) -> None:
        """пользователь отдаётся по идентификатору"""
        user = self.make_user()
        response = self.client.get(f"/api/users/{user['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["id"], user["id"])

    def test_missing(self) -> None:
        """неизвестный идентификатор даёт 404"""
        response = self.client.get(f"/api/users/{MISSING_ID}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["status"], 404)

    def test_broken_uuid(self) -> None:
        """неверный формат идентификатора даёт 404"""
        self.assertEqual(self.client.get("/api/users/abc").status_code, 404)


class CreateUserTestCase(ApiTestCase):
    """создание пользователя"""

    def test_created(self) -> None:
        """пользователь создаётся и получает uuid"""
        user = self.make_user()
        self.assertEqual(len(user["id"]), 36)
        self.assertFalse(user["is_deleted"])
        self.assertIsNone(user["deleted_at"])

    def test_accepts_flat_body(self) -> None:
        """тело без обёртки тоже принимается"""
        response = self.client.post("/api/users", json={"login": "flat", "fio": "Плоский Иван"})
        self.assertEqual(response.status_code, 200)

    def test_login_required(self) -> None:
        """логин обязателен"""
        response = self.client.post("/api/users", json={"user": {"fio": "Иванов"}})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["reason"], "Field 'login' is required")

    def test_fio_required(self) -> None:
        """фио обязательно"""
        response = self.client.post("/api/users", json={"user": {"login": "ivan"}})
        self.assertEqual(response.get_json()["reason"], "Field 'fio' is required")

    def test_blank_login_rejected(self) -> None:
        """пустая строка не считается логином"""
        response = self.client.post("/api/users", json={"user": {"login": "  ", "fio": "Иванов"}})
        self.assertEqual(response.status_code, 400)

    def test_login_too_long(self) -> None:
        """логин длиннее лимита отклоняется"""
        payload = {"user": {"login": "x" * 51, "fio": "Иванов"}}
        response = self.client.post("/api/users", json=payload)
        self.assertEqual(response.get_json()["reason"], "Field 'login' should be shorter than 50")

    def test_fio_too_long(self) -> None:
        """фио длиннее лимита отклоняется"""
        payload = {"user": {"login": "ivan", "fio": "x" * 101}}
        response = self.client.post("/api/users", json=payload)
        self.assertEqual(response.get_json()["reason"], "Field 'fio' should be shorter than 100")

    def test_duplicate_login(self) -> None:
        """логин должен быть уникальным"""
        self.make_user(login="ivan")
        response = self.client.post("/api/users", json={"user": {"login": "ivan", "fio": "Другой"}})
        self.assertEqual(response.status_code, 400)

    def test_body_must_be_object(self) -> None:
        """тело запроса должно быть объектом"""
        response = self.client.post("/api/users", json=[1, 2, 3])
        self.assertEqual(response.status_code, 400)


class UpdateUserTestCase(ApiTestCase):
    """изменение пользователя"""

    def test_updates_fio(self) -> None:
        """фио меняется"""
        user = self.make_user()
        payload = {"user": {"fio": "Новое Имя"}}
        response = self.client.patch(f"/api/users/{user['id']}", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["fio"], "Новое Имя")

    def test_keeps_untouched_fields(self) -> None:
        """непереданные поля остаются прежними"""
        user = self.make_user()
        payload = {"user": {"fio": "Новое Имя"}}
        response = self.client.patch(f"/api/users/{user['id']}", json=payload)
        self.assertEqual(response.get_json()["user"]["login"], user["login"])

    def test_missing_user(self) -> None:
        """изменение неизвестного пользователя даёт 404"""
        response = self.client.patch(f"/api/users/{MISSING_ID}", json={"user": {"fio": "x"}})
        self.assertEqual(response.status_code, 404)

    def test_duplicate_login(self) -> None:
        """чужой логин занять нельзя"""
        self.make_user(login="first")
        second = self.make_user(login="second", fio="Второй")
        payload = {"user": {"login": "first"}}
        response = self.client.patch(f"/api/users/{second['id']}", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_same_login_allowed(self) -> None:
        """свой же логин можно оставить"""
        user = self.make_user(login="ivan")
        response = self.client.patch(f"/api/users/{user['id']}", json={"user": {"login": "ivan"}})
        self.assertEqual(response.status_code, 200)

    def test_too_long_login(self) -> None:
        """слишком длинный логин отклоняется"""
        user = self.make_user()
        response = self.client.patch(f"/api/users/{user['id']}", json={"user": {"login": "x" * 51}})
        self.assertEqual(response.status_code, 400)


class DeleteUserTestCase(ApiTestCase):
    """удаление пользователя"""

    def test_returns_accepted(self) -> None:
        """успешное удаление отвечает кодом 202"""
        user = self.make_user()
        self.assertEqual(self.client.delete(f"/api/users/{user['id']}").status_code, 202)

    def test_marks_record(self) -> None:
        """запись помечается удалённой, а не стирается"""
        user = self.make_user()
        body = self.client.delete(f"/api/users/{user['id']}").get_json()["user"]
        self.assertTrue(body["is_deleted"])
        self.assertIsNotNone(body["deleted_at"])

    def test_second_delete_is_missing(self) -> None:
        """повторное удаление даёт 404"""
        user = self.make_user()
        self.client.delete(f"/api/users/{user['id']}")
        self.assertEqual(self.client.delete(f"/api/users/{user['id']}").status_code, 404)

    def test_missing_user(self) -> None:
        """удаление неизвестного пользователя даёт 404"""
        self.assertEqual(self.client.delete(f"/api/users/{MISSING_ID}").status_code, 404)

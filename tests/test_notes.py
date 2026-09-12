"""тесты эндпоинтов заметок"""

from tests.base import ApiTestCase

MISSING_ID = "11111111-1111-1111-1111-111111111111"


class ListNotesTestCase(ApiTestCase):
    """список заметок"""

    def test_empty_list(self) -> None:
        """на чистой базе список пуст"""
        response = self.client.get("/api/notes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"list": []})

    def test_list_contains_created(self) -> None:
        """созданная заметка попадает в список"""
        user = self.make_user()
        note = self.make_note(user["id"])
        titles = [item["title"] for item in self.client.get("/api/notes").get_json()["list"]]
        self.assertEqual(titles, [note["title"]])

    def test_filter_by_user(self) -> None:
        """заметки фильтруются по автору"""
        first = self.make_user(login="first")
        second = self.make_user(login="second", fio="Второй")
        self.make_note(first["id"], title="Первая")
        self.make_note(second["id"], title="Вторая")
        response = self.client.get(f"/api/notes?user_id={first['id']}")
        titles = [item["title"] for item in response.get_json()["list"]]
        self.assertEqual(titles, ["Первая"])

    def test_filter_with_broken_uuid(self) -> None:
        """фильтр с неверным идентификатором даёт 400"""
        self.assertEqual(self.client.get("/api/notes?user_id=abc").status_code, 400)

    def test_deleted_note_is_hidden(self) -> None:
        """удалённая заметка в списке не показывается"""
        user = self.make_user()
        note = self.make_note(user["id"])
        self.client.delete(f"/api/notes/{note['id']}")
        self.assertEqual(self.client.get("/api/notes").get_json(), {"list": []})


class GetNoteTestCase(ApiTestCase):
    """получение заметки"""

    def test_found(self) -> None:
        """заметка отдаётся по идентификатору"""
        user = self.make_user()
        note = self.make_note(user["id"])
        response = self.client.get(f"/api/notes/{note['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["note"]["id"], note["id"])

    def test_missing(self) -> None:
        """неизвестная заметка даёт 404"""
        self.assertEqual(self.client.get(f"/api/notes/{MISSING_ID}").status_code, 404)

    def test_broken_uuid(self) -> None:
        """неверный формат идентификатора даёт 404"""
        self.assertEqual(self.client.get("/api/notes/abc").status_code, 404)


class CreateNoteTestCase(ApiTestCase):
    """создание заметки"""

    def test_created(self) -> None:
        """заметка создаётся и связывается с автором"""
        user = self.make_user()
        note = self.make_note(user["id"])
        self.assertEqual(note["user_id"], user["id"])
        self.assertFalse(note["is_deleted"])

    def test_user_id_required(self) -> None:
        """автор обязателен"""
        response = self.client.post("/api/notes", json={"note": {"title": "a", "body": "b"}})
        self.assertEqual(response.get_json()["reason"], "Field 'user_id' is required")

    def test_title_required(self) -> None:
        """заголовок обязателен"""
        user = self.make_user()
        payload = {"note": {"user_id": user["id"], "body": "b"}}
        response = self.client.post("/api/notes", json=payload)
        self.assertEqual(response.get_json()["reason"], "Field 'title' is required")

    def test_body_required(self) -> None:
        """текст обязателен"""
        user = self.make_user()
        payload = {"note": {"user_id": user["id"], "title": "a"}}
        response = self.client.post("/api/notes", json=payload)
        self.assertEqual(response.get_json()["reason"], "Field 'body' is required")

    def test_title_too_long(self) -> None:
        """заголовок длиннее лимита отклоняется"""
        user = self.make_user()
        payload = {"note": {"user_id": user["id"], "title": "x" * 101, "body": "b"}}
        response = self.client.post("/api/notes", json=payload)
        self.assertEqual(response.get_json()["reason"], "Field 'title' should be shorter than 100")

    def test_broken_user_id(self) -> None:
        """неверный формат автора даёт 400"""
        payload = {"note": {"user_id": "abc", "title": "a", "body": "b"}}
        response = self.client.post("/api/notes", json=payload)
        self.assertEqual(response.get_json()["reason"], "Field 'user_id' should be a valid uuid")

    def test_unknown_user(self) -> None:
        """неизвестный автор даёт 400"""
        payload = {"note": {"user_id": MISSING_ID, "title": "a", "body": "b"}}
        self.assertEqual(self.client.post("/api/notes", json=payload).status_code, 400)

    def test_deleted_user_cannot_own_note(self) -> None:
        """удалённому пользователю заметку не создать"""
        user = self.make_user()
        self.client.delete(f"/api/users/{user['id']}")
        payload = {"note": {"user_id": user["id"], "title": "a", "body": "b"}}
        self.assertEqual(self.client.post("/api/notes", json=payload).status_code, 400)


class UpdateNoteTestCase(ApiTestCase):
    """изменение заметки"""

    def test_updates_title(self) -> None:
        """заголовок меняется"""
        user = self.make_user()
        note = self.make_note(user["id"])
        response = self.client.patch(f"/api/notes/{note['id']}", json={"note": {"title": "Другая"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["note"]["title"], "Другая")

    def test_keeps_untouched_fields(self) -> None:
        """непереданные поля остаются прежними"""
        user = self.make_user()
        note = self.make_note(user["id"])
        response = self.client.patch(f"/api/notes/{note['id']}", json={"note": {"title": "Другая"}})
        self.assertEqual(response.get_json()["note"]["body"], note["body"])

    def test_moves_to_another_user(self) -> None:
        """заметку можно передать другому автору"""
        first = self.make_user(login="first")
        second = self.make_user(login="second", fio="Второй")
        note = self.make_note(first["id"])
        payload = {"note": {"user_id": second["id"]}}
        response = self.client.patch(f"/api/notes/{note['id']}", json=payload)
        self.assertEqual(response.get_json()["note"]["user_id"], second["id"])

    def test_missing_note(self) -> None:
        """изменение неизвестной заметки даёт 404"""
        response = self.client.patch(f"/api/notes/{MISSING_ID}", json={"note": {"title": "x"}})
        self.assertEqual(response.status_code, 404)

    def test_unknown_user(self) -> None:
        """перенос к неизвестному автору даёт 400"""
        user = self.make_user()
        note = self.make_note(user["id"])
        payload = {"note": {"user_id": MISSING_ID}}
        response = self.client.patch(f"/api/notes/{note['id']}", json=payload)
        self.assertEqual(response.status_code, 400)


class DeleteNoteTestCase(ApiTestCase):
    """удаление заметки"""

    def test_returns_accepted(self) -> None:
        """успешное удаление отвечает кодом 202"""
        user = self.make_user()
        note = self.make_note(user["id"])
        self.assertEqual(self.client.delete(f"/api/notes/{note['id']}").status_code, 202)

    def test_marks_record(self) -> None:
        """запись помечается удалённой, а не стирается"""
        user = self.make_user()
        note = self.make_note(user["id"])
        body = self.client.delete(f"/api/notes/{note['id']}").get_json()["note"]
        self.assertTrue(body["is_deleted"])
        self.assertIsNotNone(body["deleted_at"])

    def test_second_delete_is_missing(self) -> None:
        """повторное удаление даёт 404"""
        user = self.make_user()
        note = self.make_note(user["id"])
        self.client.delete(f"/api/notes/{note['id']}")
        self.assertEqual(self.client.delete(f"/api/notes/{note['id']}").status_code, 404)

    def test_missing_note(self) -> None:
        """удаление неизвестной заметки даёт 404"""
        self.assertEqual(self.client.delete(f"/api/notes/{MISSING_ID}").status_code, 404)

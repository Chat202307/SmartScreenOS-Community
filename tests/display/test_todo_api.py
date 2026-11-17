import json

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {}


def create_app(todo_file):
    return SnapshotApplication(
        FakeHost(),
        todo_file=todo_file,
    )


def test_todo_api_lists_items(tmp_path):
    todo_file = tmp_path / "todos.json"
    todo_file.write_text(
        json.dumps(
            {
                "todos": [
                    {"title": "买牛奶", "completed": False},
                    {"title": "检查 SmartScreenOS", "completed": True},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    app = create_app(todo_file)

    status, headers, body = app.handle(
        method="GET",
        path="/api/todos",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload["todos"][0]["title"] == "买牛奶"
    assert payload["todos"][0]["completed"] is False
    assert payload["todos"][1]["completed"] is True


def test_todo_api_returns_empty_list_when_file_missing(tmp_path):
    todo_file = tmp_path / "missing.json"

    app = create_app(todo_file)

    status, headers, body = app.handle(
        method="GET",
        path="/api/todos",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload["todos"] == []
    assert isinstance(payload["revision"], str)


def test_todo_api_returns_json_content_type(tmp_path):
    todo_file = tmp_path / "todos.json"
    todo_file.write_text(
        '{"todos":[]}',
        encoding="utf-8",
    )

    app = create_app(todo_file)

    status, headers, body = app.handle(
        method="GET",
        path="/api/todos",
    )

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"


def test_todo_api_rejects_unsupported_method(tmp_path):
    todo_file = tmp_path / "todos.json"

    app = create_app(todo_file)

    status, headers, body = app.handle(
        method="PUT",
        path="/api/todos",
    )

    assert status == 405

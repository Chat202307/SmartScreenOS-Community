import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.smartscreen_display.todo_store import TodoStore, TodoError
from src.smartscreen_display.server import SnapshotApplication


def change(store, **fields):
    return store.mutate(dict(revision=store.read()["revision"], **fields))


def test_lifecycle_survives_new_store_and_preserves_ids(tmp_path):
    path = tmp_path / "new" / "todos.json"
    store = TodoStore(path)
    item = change(store, op="create", title="  买牛奶  ")["todos"][0]
    assert item["title"] == "买牛奶"
    reopened = TodoStore(path)
    assert reopened.read()["todos"][0]["id"] == item["id"]
    result = change(reopened, op="update", id=item["id"], title="买面包", completed=True)
    assert result["todos"][0]["completed"] is True
    result = change(store, op="update", id=item["id"], completed=False)
    assert result["todos"][0]["title"] == "买面包"
    assert result["todos"][0]["completed"] is False
    assert change(store, op="delete", id=item["id"])["todos"] == []


def test_legacy_read_is_non_destructive_and_first_write_backs_up(tmp_path):
    path = tmp_path / "todos.json"
    original = b'{"todos":[{"title":"original","completed":true}]}'
    path.write_bytes(original)
    store = TodoStore(path)
    first = store.read()
    assert first == TodoStore(path).read()
    assert path.read_bytes() == original
    change(store, op="create", title="second")
    assert store.read()["todos"][0]["id"] == first["todos"][0]["id"]
    change(store, op="create", title="third")
    assert path.with_name('todos.json.before-management').read_bytes() == original


@pytest.mark.parametrize("raw", ["", "[]", "null", "{", '{"todos":[null]}', '{"todos":[{"title":"x","completed":"false"}]}', '{"todos":{}}'])
def test_corrupt_storage_is_never_overwritten(tmp_path, raw):
    path = tmp_path / "todos.json"
    path.write_text(raw)
    store = TodoStore(path)
    with pytest.raises(TodoError) as exc:
        store.mutate({"op": "create", "revision": "anything", "title": "new"})
    assert exc.value.status == 503
    assert path.read_text() == raw


def test_two_screens_cannot_overwrite_each_other(tmp_path):
    store = TodoStore(tmp_path / "todos.json")
    revision = store.read()["revision"]
    def submit(title):
        try:
            store.mutate({"op": "create", "revision": revision, "title": title})
            return 200
        except TodoError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, ["one", "two"])) == [200, 409]
    assert len(store.read()["todos"]) == 1


def test_failed_replace_preserves_previous_data(tmp_path, monkeypatch):
    path = tmp_path / "todos.json"
    store = TodoStore(path)
    change(store, op="create", title="keep me")
    before = path.read_bytes()
    def fail(*args):
        raise OSError("disk error")
    monkeypatch.setattr("src.smartscreen_display.todo_store.os.replace", fail)
    with pytest.raises(TodoError) as exc:
        change(store, op="create", title="new")
    assert exc.value.code == "todo_save_failed"
    assert path.read_bytes() == before
    assert not list(tmp_path.glob('.todos-*'))


@pytest.mark.parametrize("title", ["", "  ", None, 3, "x" * 201])
def test_invalid_title_does_not_create_file(tmp_path, title):
    path = tmp_path / "todos.json"
    with pytest.raises(TodoError) as exc:
        change(TodoStore(path), op="create", title=title)
    assert exc.value.status == 400
    assert not path.exists()


def test_api_write_read_conflict_and_invalid_json(tmp_path):
    app = SnapshotApplication(object(), todo_file=tmp_path / "todos.json")
    status, _, body = app.handle(method="GET", path="/api/todos")
    revision = json.loads(body)["revision"]
    command = json.dumps({"op": "create", "revision": revision, "title": '<img src=x onerror=alert(1)>'}).encode()
    status, headers, body = app.handle(method="POST", path="/api/todos", body=command)
    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    assert json.loads(body)["todos"][0]["title"] == '<img src=x onerror=alert(1)>'
    assert app.handle(method="POST", path="/api/todos", body=command)[0] == 409
    assert app.handle(method="POST", path="/api/todos", body=b"{")[0] == 400
    assert app.handle(method="POST", path="/api/todos", body=b"x" * 4097)[0] == 413


def test_http_write_guard_and_json_round_trip(tmp_path):
    import threading
    from http.client import HTTPConnection
    from src.smartscreen_display.server import create_http_server
    app = SnapshotApplication(object(), todo_file=tmp_path / "todos.json")
    server = create_http_server(app, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    def request(method, body=None, headers=None):
        # Functional round-trip/guard test, not a three-second latency SLA.
        # Loaded CI runners can deschedule the handler beyond that interval.
        conn = HTTPConnection(host, port, timeout=30)
        try:
            conn.request(method, "/api/todos", body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()
    try:
        status, body = request("GET")
        revision = json.loads(body)["revision"]
        command = json.dumps({"op": "create", "title": "HTTP task", "revision": revision})
        assert request("POST", command, {"Content-Type": "text/plain"})[0] == 400
        assert request("POST", "x" * 4097, {"Content-Type": "application/json"})[0] == 413
        assert request("POST", command, {"Content-Type": "application/json", "Origin": "https://other.invalid"})[0] == 403
        assert request("POST", command, {"Content-Type": "application/json", "Origin": "http://["})[0] == 403
        status, body = request("POST", command, {"Content-Type": "application/json", "Origin": "http://%s:%s" % (host, port)})
        assert status == 200
        assert json.loads(body)["todos"][0]["title"] == "HTTP task"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

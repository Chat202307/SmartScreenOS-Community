import json

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {}


def create_app(home_file):
    return SnapshotApplication(
        FakeHost(),
        home_file=home_file,
    )


def test_home_status_api_lists_items(tmp_path):
    home_file = tmp_path / "home.json"
    home_file.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "name": "门窗",
                        "state": "已关闭",
                    },
                    {
                        "name": "客厅人体",
                        "state": "无人",
                    },
                    {
                        "name": "客厅灯",
                        "state": "关闭",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    app = create_app(home_file)

    status, headers, body = app.handle(
        method="GET",
        path="/api/home",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload["items"][0] == {
        "name": "门窗",
        "state": "已关闭",
    }
    assert payload["items"][1]["name"] == "客厅人体"
    assert payload["items"][2]["state"] == "关闭"


def test_home_status_api_returns_empty_when_file_missing(tmp_path):
    app = create_app(
        tmp_path / "missing.json"
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/home",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload == {
        "items": [],
    }


def test_home_status_api_returns_json_content_type(tmp_path):
    home_file = tmp_path / "home.json"
    home_file.write_text(
        '{"items":[]}',
        encoding="utf-8",
    )

    app = create_app(home_file)

    status, headers, body = app.handle(
        method="GET",
        path="/api/home",
    )

    assert status == 200
    assert (
        headers["Content-Type"]
        == "application/json; charset=utf-8"
    )


def test_home_status_api_is_read_only(tmp_path):
    app = create_app(
        tmp_path / "home.json"
    )

    status, headers, body = app.handle(
        method="POST",
        path="/api/home",
    )

    assert status == 405
    assert headers["Allow"] == "GET"


def test_home_status_api_uses_injected_provider():
    class FakeProvider:
        def get_items(self):
            return [
                {
                    "name": "测试设备",
                    "state": "在线",
                }
            ]

    app = SnapshotApplication(
        FakeHost(),
        home_provider=FakeProvider(),
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/home",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload == {
        "items": [
            {
                "name": "测试设备",
                "state": "在线",
            }
        ]
    }


def test_home_status_api_accepts_cache_busting_query(tmp_path):
    home_file = tmp_path / "home.json"
    home_file.write_text(
        '{"items":[{"name":"门窗","state":"已关闭"}]}',
        encoding="utf-8",
    )

    app = SnapshotApplication(
        FakeHost(),
        home_file=home_file,
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/home?ts=123456",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload["items"][0]["name"] == "门窗"


def test_home_status_api_exposes_provider_revision():
    class FakeProvider:
        revision = 7

        def get_items(self):
            return [
                {
                    "name": "测试设备",
                    "state": "在线",
                }
            ]

    app = SnapshotApplication(
        FakeHost(),
        home_provider=FakeProvider(),
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/home",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload == {
        "items": [
            {
                "name": "测试设备",
                "state": "在线",
            }
        ],
        "revision": 7,
    }


def test_home_status_events_endpoint_exists():
    app = SnapshotApplication(
        FakeHost(),
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/home/events",
    )

    assert status == 200


def test_home_status_events_uses_event_stream_content_type():
    app = SnapshotApplication(
        FakeHost(),
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/home/events",
    )

    assert status == 200
    assert (
        headers["Content-Type"]
        == "text/event-stream; charset=utf-8"
    )


def test_home_status_api_exposes_provider_availability():
    class AvailabilityProvider:
        revision = 7
        available = False

        def get_items(self):
            return [
                {
                    "name": "客厅主灯",
                    "state": "关闭",
                }
            ]

    app = SnapshotApplication(
        FakeHost(),
        home_provider=AvailabilityProvider(),
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/home",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200

    assert payload == {
        "items": [
            {
                "name": "客厅主灯",
                "state": "关闭",
            }
        ],
        "revision": 7,
        "available": False,
    }


def test_home_status_api_defaults_available_when_provider_has_no_availability_contract():
    class LegacyProvider:
        revision = 3

        def get_items(self):
            return []

    app = SnapshotApplication(
        FakeHost(),
        home_provider=LegacyProvider(),
    )

    _, _, body = app.handle(
        method="GET",
        path="/api/home",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert "available" not in payload

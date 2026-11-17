import json

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {
            "schemaVersion": "1.0",
            "generatedAt": "2026-08-07T14:45:00+00:00",
            "runtime": {
                "installed": [],
                "sessions": [],
            },
            "scheduler": {
                "running": True,
                "backgroundRunning": True,
                "backgroundFailed": False,
                "lastBackgroundError": None,
                "intervalSeconds": 1.0,
                "nextRunAt": 100.0,
            },
            "capabilities": {},
        }


def test_snapshot_endpoint_returns_json():
    app = SnapshotApplication(FakeHost())

    status, headers, body = app.handle(
        method="GET",
        path="/api/snapshot",
    )

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"

    payload = json.loads(body.decode("utf-8"))

    assert payload["schemaVersion"] == "1.0"


def test_unknown_endpoint_returns_404():
    app = SnapshotApplication(FakeHost())

    status, headers, body = app.handle(
        method="GET",
        path="/unknown",
    )

    assert status == 404


def test_snapshot_endpoint_rejects_post():
    app = SnapshotApplication(FakeHost())

    status, headers, body = app.handle(
        method="POST",
        path="/api/snapshot",
    )

    assert status == 405


def test_snapshot_json_keeps_chinese_text():
    class ChineseHost:
        def snapshot(self):
            return {
                "condition": "晴",
            }

    app = SnapshotApplication(ChineseHost())

    status, headers, body = app.handle(
        method="GET",
        path="/api/snapshot",
    )

    assert status == 200
    assert "晴" in body.decode("utf-8")

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {
            "schemaVersion": "1.0",
            "capabilities": {},
        }


def test_root_returns_dashboard_html():
    app = SnapshotApplication(FakeHost())

    status, headers, body = app.handle(
        method="GET",
        path="/",
    )

    assert status == 200
    assert headers["Content-Type"] == "text/html; charset=utf-8"

    html = body.decode("utf-8")

    assert "<!doctype html>" in html.lower()
    assert "<title>SmartScreenOS</title>" in html
    assert "SmartScreenOS" in html


def test_snapshot_endpoint_still_returns_json():
    app = SnapshotApplication(FakeHost())

    status, headers, body = app.handle(
        method="GET",
        path="/api/snapshot",
    )

    assert status == 200
    assert headers["Content-Type"] == "application/json; charset=utf-8"

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {
            "schemaVersion": "1.0",
            "capabilities": {},
        }


def create_app():
    return SnapshotApplication(FakeHost())


def test_dashboard_css_is_served():
    app = create_app()

    status, headers, body = app.handle(
        method="GET",
        path="/static/dashboard.css",
    )

    assert status == 200
    assert headers["Content-Type"] == "text/css; charset=utf-8"
    assert b".dashboard" in body
    assert b"#time" in body


def test_dashboard_javascript_is_served():
    app = create_app()

    status, headers, body = app.handle(
        method="GET",
        path="/static/dashboard.js",
    )

    assert status == 200
    assert headers["Content-Type"] == "application/javascript; charset=utf-8"
    assert b"XMLHttpRequest" in body
    assert b"/api/snapshot" in body


def test_dashboard_references_static_assets():
    app = create_app()

    status, headers, body = app.handle(
        method="GET",
        path="/",
    )

    html = body.decode("utf-8")

    assert status == 200
    assert 'href="/static/dashboard.css?v=79"' in html
    assert 'src="/static/dashboard.js?v=60"' in html


def test_unknown_static_asset_returns_404():
    app = create_app()

    status, headers, body = app.handle(
        method="GET",
        path="/static/missing.css",
    )

    assert status == 404


def test_static_assets_are_read_only():
    app = create_app()

    status, headers, body = app.handle(
        method="POST",
        path="/static/dashboard.css",
    )

    assert status == 405
    assert headers["Allow"] == "GET"

import json
from datetime import datetime, timezone

from src.smartscreen_display.server import SnapshotApplication
from src.smartscreen_runtime.runtime.bootstrap import (
    create_runtime_host_from_config,
)


class FakeWeatherProvider:
    def fetch(self, location: str) -> dict:
        return {
            "condition": "sunny",
            "temperature": 26.0,
            "humidity": 58,
            "windSpeed": 12.0,
            "observedAt": datetime(
                2026,
                8,
                8,
                20,
                0,
                tzinfo=timezone.utc,
            ),
        }


def create_app():
    host = create_runtime_host_from_config(
        "config/runtime.test.yaml"
    )

    weather = host.engine.get_instance(
        "session-weather-main"
    )
    weather.set_provider(FakeWeatherProvider())

    host.engine.tick()

    return host, SnapshotApplication(host)


def test_display_v1_root_page():
    host, app = create_app()

    try:
        status, headers, body = app.handle(
            method="GET",
            path="/",
        )

        assert status == 200
        assert headers["Content-Type"] == "text/html; charset=utf-8"

        html = body.decode("utf-8")

        assert "<title>SmartScreenOS</title>" in html
        assert 'href="/static/dashboard.css?v=79"' in html
        assert 'src="/static/dashboard.js?v=60"' in html

    finally:
        for session in host.engine.sessions.list():
            if session.state.value == "running":
                host.engine.stop(session.session_id)


def test_display_v1_static_assets():
    host, app = create_app()

    try:
        css_status, _, css = app.handle(
            method="GET",
            path="/static/dashboard.css",
        )
        js_status, _, script = app.handle(
            method="GET",
            path="/static/dashboard.js",
        )

        assert css_status == 200
        assert js_status == 200

        assert b".dashboard" in css
        assert b"XMLHttpRequest" in script
        assert b"weather_status" in script

    finally:
        for session in host.engine.sessions.list():
            if session.state.value == "running":
                host.engine.stop(session.session_id)


def test_display_v1_snapshot_api():
    host, app = create_app()

    try:
        status, headers, body = app.handle(
            method="GET",
            path="/api/snapshot",
        )

        assert status == 200
        assert (
            headers["Content-Type"]
            == "application/json; charset=utf-8"
        )

        payload = json.loads(body.decode("utf-8"))

        assert payload["schemaVersion"] == "1.0"

        assert (
            payload["capabilities"]
            ["session-clock-main"]
            ["timezone"]
            == "Asia/Shanghai"
        )

        weather = payload["capabilities"][
            "session-weather-main"
        ]

        assert weather["condition"] == "sunny"
        assert weather["temperature"] == 26.0
        assert weather["humidity"] == 58
        assert weather["windSpeed"] == 12.0

    finally:
        for session in host.engine.sessions.list():
            if session.state.value == "running":
                host.engine.stop(session.session_id)

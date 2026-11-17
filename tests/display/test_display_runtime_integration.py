import json
from datetime import datetime, timezone
from http.client import HTTPConnection
from threading import Thread

from src.smartscreen_display.server import (
    SnapshotApplication,
    create_http_server,
)
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
                7,
                21,
                0,
                tzinfo=timezone.utc,
            ),
        }


def test_http_server_serves_real_runtime_host_snapshot():
    host = create_runtime_host_from_config(
        "config/runtime.test.yaml"
    )

    weather = host.engine.get_instance(
        "session-weather-main"
    )
    weather.set_provider(FakeWeatherProvider())

    host.engine.tick()

    app = SnapshotApplication(host)

    server = create_http_server(
        app,
        host="127.0.0.1",
        port=0,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        address, port = server.server_address

        connection = HTTPConnection(
            address,
            port,
            timeout=2,
        )
        connection.request(
            "GET",
            "/api/snapshot",
        )

        response = connection.getresponse()
        body = response.read()

        assert response.status == 200

        payload = json.loads(
            body.decode("utf-8")
        )

        assert payload["schemaVersion"] == "1.0"

        assert (
            payload["capabilities"]
            ["session-clock-main"]
            ["timezone"]
            == "Asia/Shanghai"
        )

        assert (
            payload["capabilities"]
            ["session-weather-main"]
            ["condition"]
            == "sunny"
        )

        assert (
            payload["capabilities"]
            ["session-weather-main"]
            ["temperature"]
            == 26.0
        )

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)

        for session in host.engine.sessions.list():
            if session.state.value == "running":
                host.engine.stop(
                    session.session_id
                )

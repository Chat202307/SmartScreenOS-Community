from http.client import HTTPConnection
from threading import Event, Thread

from src.smartscreen_display.server import (
    SnapshotApplication,
    create_http_server,
)


class FakeHost:
    def snapshot(self):
        return {
            "schemaVersion": "1",
            "generatedAt": "2026-08-12T00:00:00+00:00",
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


def test_http_server_streams_dashboard_state_event():
    class FakeNotifier:
        revision = 4

        def __init__(self):
            self.wait_called = Event()

        def wait_for_change(
            self,
            revision,
            *,
            timeout=None,
        ):
            assert revision == 4
            self.wait_called.set()
            return 5

    notifier = FakeNotifier()

    app = SnapshotApplication(
        FakeHost(),
    )

    server = create_http_server(
        app,
        host="127.0.0.1",
        port=0,
        dashboard_state_notifier=notifier,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "GET",
            "/api/dashboard/events",
        )

        response = connection.getresponse()

        assert response.status == 200
        assert (
            response.getheader("Content-Type")
            == "text/event-stream; charset=utf-8"
        )

        assert notifier.wait_called.wait(
            timeout=1.0
        )

        assert response.readline() == (
            b"event: dashboard-state-changed\n"
        )
        assert response.readline() == (
            b'data: {"revision":5}\n'
        )
        assert response.readline() == b"\n"

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


def test_http_server_streams_multiple_dashboard_state_events():
    class FakeNotifier:
        revision = 10

        def __init__(self):
            self.calls = 0
            self.second_event_sent = Event()

        def wait_for_change(
            self,
            revision,
            *,
            timeout=None,
        ):
            self.calls += 1

            if self.calls == 1:
                assert revision == 10
                return 11

            if self.calls == 2:
                assert revision == 11
                self.second_event_sent.set()
                return 12

            return revision

    notifier = FakeNotifier()

    app = SnapshotApplication(
        FakeHost(),
    )

    server = create_http_server(
        app,
        host="127.0.0.1",
        port=0,
        dashboard_state_notifier=notifier,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )

        connection.request(
            "GET",
            "/api/dashboard/events",
        )

        response = connection.getresponse()

        assert response.status == 200

        assert response.readline() == (
            b"event: dashboard-state-changed\n"
        )
        assert response.readline() == (
            b'data: {"revision":11}\n'
        )
        assert response.readline() == b"\n"

        assert response.readline() == (
            b"event: dashboard-state-changed\n"
        )
        assert response.readline() == (
            b'data: {"revision":12}\n'
        )
        assert response.readline() == b"\n"

        assert notifier.second_event_sent.wait(
            timeout=1.0
        )

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)

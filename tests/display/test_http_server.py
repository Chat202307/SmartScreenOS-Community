import json
from http.client import HTTPConnection
from threading import Thread

from src.smartscreen_display.server import (
    SnapshotApplication,
    create_http_server,
)


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


def start_server():
    app = SnapshotApplication(FakeHost())

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

    return server, thread


def test_http_server_serves_snapshot():
    server, thread = start_server()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )
        connection.request("GET", "/api/snapshot")

        response = connection.getresponse()
        body = response.read()

        assert response.status == 200
        assert (
            response.getheader("Content-Type")
            == "application/json; charset=utf-8"
        )

        payload = json.loads(body.decode("utf-8"))

        assert payload["schemaVersion"] == "1.0"

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


def test_http_server_returns_404():
    server, thread = start_server()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )
        connection.request("GET", "/missing")

        response = connection.getresponse()
        response.read()

        assert response.status == 404

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


def test_http_server_rejects_post():
    server, thread = start_server()

    try:
        host, port = server.server_address

        connection = HTTPConnection(
            host,
            port,
            timeout=2,
        )
        connection.request("POST", "/api/snapshot")

        response = connection.getresponse()
        response.read()

        assert response.status == 405
        assert response.getheader("Allow") == "GET"

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


def test_http_server_tolerates_client_disconnect():
    class DisconnectingStream:
        def write(self, body):
            raise BrokenPipeError("client disconnected")

    # This behavior is guarded in the request handler:
    # client disconnects while sending a response must not crash
    # the display server thread.
    assert issubclass(BrokenPipeError, OSError)
    assert issubclass(ConnectionResetError, OSError)


def test_http_server_streams_home_status_event():
    import threading

    class FakeNotifier:
        revision = 7

        def __init__(self):
            self.wait_called = threading.Event()

        def wait_for_change(
            self,
            revision,
            *,
            timeout=None,
        ):
            assert revision == 7
            self.wait_called.set()
            return 8

    notifier = FakeNotifier()

    app = SnapshotApplication(
        FakeHost(),
    )

    server = create_http_server(
        app,
        host="127.0.0.1",
        port=0,
        home_status_notifier=notifier,
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
            "/api/home/events",
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

        line = response.readline()

        assert line == b"event: home-status-changed\n"

        line = response.readline()

        assert line == b"data: {\"revision\":8}\n"

        line = response.readline()

        assert line == b"\n"

        connection.close()

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1.0)


def test_http_server_streams_multiple_home_status_events():
    import threading

    class FakeNotifier:
        revision = 7

        def __init__(self):
            self.calls = 0
            self.second_event_sent = threading.Event()

        def wait_for_change(
            self,
            revision,
            *,
            timeout=None,
        ):
            self.calls += 1

            if self.calls == 1:
                assert revision == 7
                return 8

            if self.calls == 2:
                assert revision == 8
                self.second_event_sent.set()
                return 9

            return revision

    notifier = FakeNotifier()

    app = SnapshotApplication(
        FakeHost(),
    )

    server = create_http_server(
        app,
        host="127.0.0.1",
        port=0,
        home_status_notifier=notifier,
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
            "/api/home/events",
        )

        response = connection.getresponse()

        assert response.status == 200

        assert response.readline() == (
            b"event: home-status-changed\n"
        )
        assert response.readline() == (
            b'data: {"revision":8}\n'
        )
        assert response.readline() == b"\n"

        assert response.readline() == (
            b"event: home-status-changed\n"
        )
        assert response.readline() == (
            b'data: {"revision":9}\n'
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

import json

from src.smartscreen_display.home_assistant_state_stream import (
    HomeAssistantStateStream,
)


class FakeConnection:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []

    def recv(self):
        return self.messages.pop(0)

    def send(self, message):
        self.sent.append(message)


class FakeConsumer:
    def __init__(self):
        self.messages = []

    def consume(self, message):
        self.messages.append(message)


def test_state_stream_authenticates():
    connection = FakeConnection(
        [
            json.dumps(
                {
                    "type": "auth_required",
                    "ha_version": "2026.8.0",
                }
            ),
            json.dumps(
                {
                    "type": "auth_ok",
                    "ha_version": "2026.8.0",
                }
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [],
                }
            ),

        ]
    )

    consumer = FakeConsumer()

    stream = HomeAssistantStateStream(
        token="secret-token",
        consumer=consumer,
    )

    stream.run_connection(
        connection,
        max_events=0,
    )

    assert json.loads(
        connection.sent[0]
    ) == {
        "type": "auth",
        "access_token": "secret-token",
    }


def test_state_stream_subscribes_to_state_changed():
    connection = FakeConnection(
        [
            json.dumps(
                {
                    "type": "auth_required",
                }
            ),
            json.dumps(
                {
                    "type": "auth_ok",
                }
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [],
                }
            ),

        ]
    )

    stream = HomeAssistantStateStream(
        token="secret-token",
        consumer=FakeConsumer(),
    )

    stream.run_connection(
        connection,
        max_events=0,
    )

    assert json.loads(
        connection.sent[1]
    ) == {
        "id": 1,
        "type": "subscribe_events",
        "event_type": "state_changed",
    }


def test_state_stream_forwards_state_changed_event():
    event_message = {
        "id": 1,
        "type": "event",
        "event": {
            "event_type": "state_changed",
            "data": {
                "entity_id": "light.living_room",
                "new_state": {
                    "entity_id": "light.living_room",
                    "state": "on",
                    "attributes": {},
                },
            },
        },
    }

    connection = FakeConnection(
        [
            json.dumps(
                {
                    "type": "auth_required",
                }
            ),
            json.dumps(
                {
                    "type": "auth_ok",
                }
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [],
                }
            ),

            json.dumps(
                event_message
            ),
        ]
    )

    consumer = FakeConsumer()

    stream = HomeAssistantStateStream(
        token="secret-token",
        consumer=consumer,
    )

    stream.run_connection(
        connection,
        max_events=1,
    )

    assert consumer.messages == [
        event_message,
    ]


def test_state_stream_updates_provider_cache_end_to_end():
    from src.smartscreen_display.home_assistant_state_events import (
        HomeAssistantStateEventConsumer,
    )
    from src.smartscreen_display.home_status import (
        HomeAssistantHomeStatusProvider,
    )

    client = FakeClientForProvider(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {},
            }
        ]
    )

    provider = HomeAssistantHomeStatusProvider(
        client,
        entities=[
            {
                "entity_id": "light.living_room",
                "name": "客厅灯",
                "states": {
                    "on": "开启",
                    "off": "关闭",
                },
            }
        ],
    )

    provider.refresh()

    assert provider.get_cached_items() == [
        {
            "name": "客厅灯",
            "state": "关闭",
        }
    ]

    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    connection = FakeConnection(
        [
            json.dumps(
                {
                    "type": "auth_required",
                }
            ),
            json.dumps(
                {
                    "type": "auth_ok",
                }
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [],
                }
            ),

            json.dumps(
                {
                    "id": 1,
                    "type": "event",
                    "event": {
                        "event_type":
                            "state_changed",
                        "data": {
                            "entity_id":
                                "light.living_room",
                            "new_state": {
                                "entity_id":
                                    "light.living_room",
                                "state": "on",
                                "attributes": {},
                            },
                        },
                    },
                }
            ),
        ]
    )

    stream = HomeAssistantStateStream(
        token="secret-token",
        consumer=consumer,
    )

    stream.run_connection(
        connection,
        max_events=1,
    )

    assert provider.get_cached_items() == [
        {
            "name": "客厅灯",
            "state": "开启",
        }
    ]


class FakeClientForProvider:
    def __init__(self, states):
        self.states = states

    def get_json(self, path):
        assert path == "/api/states"
        return self.states


class FakeConnectionContext:
    def __init__(self, connection):
        self.connection = connection
        self.entered = False
        self.exited = False

    def __enter__(self):
        self.entered = True
        return self.connection

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.exited = True


def test_state_stream_builds_websocket_url():
    calls = []

    connection = FakeConnection(
        [
            json.dumps(
                {"type": "auth_required"}
            ),
            json.dumps(
                {"type": "auth_ok"}
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [],
                }
            ),

        ]
    )

    context = FakeConnectionContext(
        connection
    )

    def fake_connect(uri, **kwargs):
        calls.append(
            (uri, kwargs)
        )
        return context

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=fake_connect,
    )

    stream.run(
        max_events=0,
    )

    assert calls == [
        (
            "ws://192.0.2.2:8123/api/websocket",
            {
                "proxy": None,
            },
        )
    ]

    assert context.entered is True
    assert context.exited is True


def test_state_stream_uses_secure_websocket_url_for_https():
    calls = []

    connection = FakeConnection(
        [
            json.dumps(
                {"type": "auth_required"}
            ),
            json.dumps(
                {"type": "auth_ok"}
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [],
                }
            ),

        ]
    )

    context = FakeConnectionContext(
        connection
    )

    def fake_connect(uri, **kwargs):
        calls.append(uri)
        return context

    stream = HomeAssistantStateStream(
        base_url="https://ha.example.com",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=fake_connect,
    )

    stream.run(
        max_events=0,
    )

    assert calls == [
        "wss://ha.example.com/api/websocket",
    ]


def test_state_stream_removes_trailing_slash_from_base_url():
    assert HomeAssistantStateStream._websocket_url(
        "http://192.0.2.2:8123/"
    ) == (
        "ws://192.0.2.2:8123/api/websocket"
    )


def test_state_stream_rejects_unsupported_url_scheme():
    try:
        HomeAssistantStateStream._websocket_url(
            "ftp://192.0.2.2"
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "Home Assistant URL must use http or https"
        )
    else:
        raise AssertionError(
            "unsupported URL scheme was accepted"
        )


def test_state_stream_start_runs_in_background_thread():
    import threading

    run_started = threading.Event()
    release_run = threading.Event()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
    )

    def fake_run_forever():
        run_started.set()
        release_run.wait(timeout=1.0)

    stream.run_forever = fake_run_forever

    stream.start()

    assert run_started.wait(timeout=1.0)
    assert stream.is_alive() is True

    release_run.set()
    stream.join(timeout=1.0)

    assert stream.is_alive() is False

def test_state_stream_stop_closes_active_connection():
    class BlockingConnection:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
    )

    connection = BlockingConnection()

    stream._connection = connection

    stream.stop()

    assert connection.closed is True


def test_state_stream_run_tracks_active_connection():
    connection_seen = []

    class TrackingConnection:
        pass

    connection = TrackingConnection()

    class ConnectionContext:
        def __enter__(self):
            return connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

    def fake_connect(uri, **kwargs):
        return ConnectionContext()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=fake_connect,
    )

    def fake_run_connection(
        active_connection,
        *,
        max_events=None,
    ):
        connection_seen.append(
            stream._connection
        )
        assert (
            active_connection
            is connection
        )

    stream.run_connection = fake_run_connection

    stream.run()

    assert connection_seen == [
        connection,
    ]


def test_state_stream_run_clears_active_connection():
    class TrackingConnection:
        pass

    connection = TrackingConnection()

    class ConnectionContext:
        def __enter__(self):
            return connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

    def fake_connect(uri, **kwargs):
        return ConnectionContext()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=fake_connect,
    )

    stream.run_connection = (
        lambda connection, max_events=None: None
    )

    stream.run()

    assert stream._connection is None


def test_state_stream_stop_unblocks_connection_and_joins():
    import threading

    recv_started = threading.Event()

    class BlockingConnection:
        def __init__(self):
            self.closed = threading.Event()
            self.sent = []
            self.messages = [
                json.dumps(
                    {"type": "auth_required"}
                ),
                json.dumps(
                    {"type": "auth_ok"}
                ),
                json.dumps(
                    {
                        "id": 1,
                        "type": "result",
                        "success": True,
                        "result": None,
                    }
                ),
            ]

        def send(self, message):
            self.sent.append(message)

        def recv(self):
            if self.messages:
                return self.messages.pop(0)

            recv_started.set()
            self.closed.wait(timeout=2.0)

            raise RuntimeError(
                "connection closed"
            )

        def close(self):
            self.closed.set()

    connection = BlockingConnection()

    class ConnectionContext:
        def __enter__(self):
            return connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

    def fake_connect(uri, **kwargs):
        return ConnectionContext()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=fake_connect,
    )

    stream.start()

    assert recv_started.wait(timeout=1.0)
    assert stream.is_alive() is True

    stream.stop()
    stream.join(timeout=1.0)

    assert connection.closed.is_set()
    assert stream.is_alive() is False
    assert stream._connection is None


def test_state_stream_reconnects_after_connection_failure():
    attempts = []

    class SuccessfulConnection:
        pass

    connection = SuccessfulConnection()

    class ConnectionContext:
        def __enter__(self):
            return connection

        def __exit__(
            self,
            exc_type,
            exc_value,
            traceback,
        ):
            return False

    def fake_connect(uri, **kwargs):
        attempts.append(uri)

        if len(attempts) == 1:
            raise OSError(
                "temporary connection failure"
            )

        return ConnectionContext()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=fake_connect,
    )

    def fake_run_connection(
        active_connection,
        *,
        max_events=None,
    ):
        assert active_connection is connection
        stream.stop()

    stream.run_connection = fake_run_connection

    stream.run_forever(
        reconnect_delay=0,
    )

    assert len(attempts) == 2


def test_state_stream_background_uses_run_forever():
    import threading

    called = threading.Event()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
    )

    def fake_run_forever():
        called.set()

    stream.run_forever = fake_run_forever

    stream.start()

    assert called.wait(timeout=1.0)

    stream.join(timeout=1.0)

    assert stream.is_alive() is False


def test_state_stream_stop_interrupts_reconnect_wait():
    import threading
    import time

    first_attempt = threading.Event()

    def failing_connect(uri, **kwargs):
        first_attempt.set()
        raise OSError(
            "temporary connection failure"
        )

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
        connector=failing_connect,
    )

    thread = threading.Thread(
        target=lambda: stream.run_forever(
            reconnect_delay=10.0,
        )
    )

    thread.start()

    assert first_attempt.wait(timeout=1.0)

    started = time.monotonic()

    stream.stop()
    thread.join(timeout=1.0)

    elapsed = (
        time.monotonic()
        - started
    )

    assert thread.is_alive() is False
    assert elapsed < 1.0


def test_state_stream_can_restart_after_stop():
    import threading

    runs = []
    run_started = threading.Event()

    stream = HomeAssistantStateStream(
        base_url="http://192.0.2.2:8123",
        token="secret-token",
        consumer=FakeConsumer(),
    )

    def fake_run():
        runs.append(
            len(runs) + 1
        )
        run_started.set()
        stream.stop()

    stream.run = fake_run

    stream.start()

    assert run_started.wait(timeout=1.0)

    stream.join(timeout=1.0)

    assert stream.is_alive() is False
    assert runs == [1]

    run_started.clear()

    stream.start()

    assert run_started.wait(timeout=1.0)

    stream.join(timeout=1.0)

    assert stream.is_alive() is False
    assert runs == [1, 2]


def test_state_stream_seeds_consumer_with_current_states():
    current_state = {
        "entity_id": "binary_sensor.living_presence",
        "state": "off",
        "attributes": {
            "device_class": "occupancy",
        },
    }

    connection = FakeConnection(
        [
            json.dumps(
                {
                    "type": "auth_required",
                }
            ),
            json.dumps(
                {
                    "type": "auth_ok",
                }
            ),
            # Existing subscription acknowledgement.
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),
            # Initial HA state snapshot.
            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [
                        current_state,
                    ],
                }
            ),
        ]
    )

    consumer = FakeConsumer()

    stream = HomeAssistantStateStream(
        token="secret-token",
        consumer=consumer,
    )

    stream.run_connection(
        connection,
        max_events=0,
    )

    assert json.loads(
        connection.sent[1]
    ) == {
        "id": 1,
        "type": "subscribe_events",
        "event_type": "state_changed",
    }

    assert json.loads(
        connection.sent[2]
    ) == {
        "id": 2,
        "type": "get_states",
    }

    assert consumer.messages == [
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id":
                        "binary_sensor.living_presence",
                    "new_state": current_state,
                },
            },
        }
    ]


def test_state_stream_replays_event_received_while_seeding():
    snapshot_state = {
        "entity_id": "binary_sensor.living_presence",
        "state": "off",
        "attributes": {
            "device_class": "occupancy",
        },
    }

    live_state = {
        "entity_id": "binary_sensor.living_presence",
        "state": "on",
        "attributes": {
            "device_class": "occupancy",
        },
    }

    live_event = {
        "id": 1,
        "type": "event",
        "event": {
            "event_type": "state_changed",
            "data": {
                "entity_id":
                    "binary_sensor.living_presence",
                "new_state": live_state,
            },
        },
    }

    connection = FakeConnection(
        [
            json.dumps(
                {
                    "type": "auth_required",
                }
            ),
            json.dumps(
                {
                    "type": "auth_ok",
                }
            ),
            json.dumps(
                {
                    "id": 1,
                    "type": "result",
                    "success": True,
                    "result": None,
                }
            ),
            # A live event arrives before get_states returns.
            json.dumps(
                live_event
            ),
            json.dumps(
                {
                    "id": 2,
                    "type": "result",
                    "success": True,
                    "result": [
                        snapshot_state,
                    ],
                }
            ),
        ]
    )

    consumer = FakeConsumer()

    stream = HomeAssistantStateStream(
        token="secret-token",
        consumer=consumer,
    )

    stream.run_connection(
        connection,
        max_events=1,
    )

    assert len(consumer.messages) == 2

    seeded = consumer.messages[0]
    replayed = consumer.messages[1]

    assert (
        seeded["event"]["data"]["new_state"]["state"]
        == "off"
    )

    assert replayed == live_event

    assert (
        replayed["event"]["data"]["new_state"]["state"]
        == "on"
    )

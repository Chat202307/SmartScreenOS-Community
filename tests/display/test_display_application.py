from pathlib import Path

import pytest

from src.smartscreen_display.application import (
    run_display_server,
)


@pytest.fixture(autouse=True)
def clear_home_assistant_environment(
    monkeypatch,
):
    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    for variable in (
        "SMARTSCREEN_XINGOO_TOKEN",
        "SMARTSCREEN_XINGOO_USERNAME",
        "SMARTSCREEN_XINGOO_PASSWORD",
    ):
        monkeypatch.delenv(
            variable,
            raising=False,
        )


class FakeRuntimeHost:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.joined = False

    def start_background(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout=None) -> None:
        self.joined = True

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


class FakeHttpServer:
    def __init__(self) -> None:
        self.served = False
        self.shutdown_called = False
        self.closed = False

    def serve_forever(self) -> None:
        self.served = True
        raise KeyboardInterrupt

    def shutdown(self) -> None:
        self.shutdown_called = True

    def server_close(self) -> None:
        self.closed = True


def test_run_display_server_starts_runtime_and_http_server():
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        assert host == "127.0.0.1"
        assert port == 8080
        return server

    result = run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert result == 0
    assert runtime.started is True
    assert server.served is True
    assert runtime.stopped is True
    assert runtime.joined is True
    assert server.closed is True


def test_run_display_server_accepts_bind_address():
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["host"] = host
        captured["port"] = port
        return server

    run_display_server(
        bind_host="0.0.0.0",
        port=9090,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured == {
        "host": "0.0.0.0",
        "port": 9090,
    }


def test_run_display_server_uses_custom_photo_dir(tmp_path):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["photo_dir"] = app._photo_dir
        return server

    run_display_server(
        photo_dir=tmp_path,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["photo_dir"] == tmp_path.resolve()


def test_main_accepts_photo_dir(monkeypatch, tmp_path):
    from src.smartscreen_display import application

    captured = {}

    def fake_run_display_server(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_display_server",
        fake_run_display_server,
    )

    result = application.main(
        [
            "--photo-dir",
            str(tmp_path),
        ]
    )

    assert result == 0
    assert captured["photo_dir"] == tmp_path


def test_run_display_server_uses_custom_todo_file(tmp_path):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    todo_file = tmp_path / "todos.json"

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["todo_file"] = app._todo_file
        return server

    run_display_server(
        todo_file=todo_file,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["todo_file"] == todo_file.resolve()


def test_main_accepts_todo_file(monkeypatch, tmp_path):
    from src.smartscreen_display import application

    captured = {}
    todo_file = tmp_path / "todos.json"

    def fake_run_display_server(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_display_server",
        fake_run_display_server,
    )

    result = application.main(
        [
            "--todo-file",
            str(todo_file),
        ]
    )

    assert result == 0
    assert captured["todo_file"] == todo_file


def test_run_display_server_uses_custom_home_file(tmp_path):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    home_file = tmp_path / "home.json"

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["home_file"] = app._home_provider._path
        return server

    run_display_server(
        home_file=home_file,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["home_file"] == home_file.resolve()


def test_main_accepts_home_file(monkeypatch, tmp_path):
    from src.smartscreen_display import application

    captured = {}
    home_file = tmp_path / "home.json"

    def fake_run_display_server(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_display_server",
        fake_run_display_server,
    )

    result = application.main(
        [
            "--home-file",
            str(home_file),
        ]
    )

    assert result == 0
    assert captured["home_file"] == home_file


def test_display_uses_home_assistant_provider_when_available(
    monkeypatch,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    class FakeProvider:
        pass

    provider = FakeProvider()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: provider,
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["provider"] = app._home_provider
        return server

    run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["provider"] is provider


def test_display_falls_back_to_home_file_without_ha(
    monkeypatch,
    tmp_path,
):
    for key in (
        "SMARTSCREEN_XINGOO_TOKEN",
        "SMARTSCREEN_XINGOO_USERNAME",
        "SMARTSCREEN_XINGOO_PASSWORD",
    ):
        monkeypatch.delenv(
            key,
            raising=False,
        )

    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    home_file = tmp_path / "home.json"

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda: None,
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["path"] = app._home_provider._path
        return server

    run_display_server(
        home_file=home_file,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["path"] == home_file.resolve()


def test_explicit_home_file_overrides_home_assistant_provider(
    monkeypatch,
    tmp_path,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    home_file = tmp_path / "home.json"

    class FakeHomeAssistantProvider:
        pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda: FakeHomeAssistantProvider(),
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["provider"] = app._home_provider
        return server

    run_display_server(
        home_file=home_file,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["provider"]._path == home_file.resolve()


def test_run_display_server_passes_home_entities_file_to_ha_source(
    monkeypatch,
    tmp_path,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    entities_file = tmp_path / "entities.json"

    class FakeProvider:
        pass

    provider = FakeProvider()

    def fake_create_home_assistant_provider(**kwargs):
        captured.update(kwargs)
        return provider

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        fake_create_home_assistant_provider,
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        return server

    run_display_server(
        home_entities_file=entities_file,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert (
        captured["entities_file"]
        == entities_file
    )


def test_main_accepts_home_entities_file(
    monkeypatch,
    tmp_path,
):
    from src.smartscreen_display import application

    captured = {}
    entities_file = tmp_path / "entities.json"

    def fake_run_display_server(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_display_server",
        fake_run_display_server,
    )

    result = application.main(
        [
            "--home-entities-file",
            str(entities_file),
        ]
    )

    assert result == 0
    assert (
        captured["home_entities_file"]
        == entities_file
    )


def test_explicit_home_file_skips_ha_entity_config(
    monkeypatch,
    tmp_path,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()

    home_file = tmp_path / "home.json"
    entities_file = tmp_path / "entities.json"

    called = {
        "ha_source": False,
    }

    def fake_create_home_assistant_provider(**kwargs):
        called["ha_source"] = True
        return None

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        fake_create_home_assistant_provider,
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        return server

    run_display_server(
        home_file=home_file,
        home_entities_file=entities_file,
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert called["ha_source"] is False


def test_display_uses_project_home_entities_config_by_default(
    monkeypatch,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    class FakeProvider:
        pass

    def fake_create_home_assistant_provider(**kwargs):
        captured.update(kwargs)
        return FakeProvider()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        fake_create_home_assistant_provider,
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        return server

    run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert captured["entities_file"] == Path(
        "config/home_entities.json"
    )


def test_run_display_server_manages_home_assistant_state_stream():
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()

    class FakeStateStream:
        def __init__(self):
            self.started = False
            self.stopped = False
            self.joined = False
            self.join_timeout = None

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def join(self, timeout=None):
            self.joined = True
            self.join_timeout = timeout

    state_stream = FakeStateStream()

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        return server

    result = run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
        state_stream=state_stream,
    )

    assert result == 0
    assert state_stream.started is True
    assert state_stream.stopped is True
    assert state_stream.joined is True
    assert state_stream.join_timeout == 5.0


def test_run_display_server_orders_state_stream_lifecycle():
    events = []

    class OrderedRuntime:
        def start_background(self):
            events.append("runtime.start")

        def stop(self):
            events.append("runtime.stop")

        def join(self, timeout=None):
            events.append("runtime.join")

        def snapshot(self):
            return {}

    class OrderedStateStream:
        def start(self):
            events.append("stream.start")

        def stop(self):
            events.append("stream.stop")

        def join(self, timeout=None):
            events.append("stream.join")

    class OrderedServer:
        def serve_forever(self):
            events.append("server.serve")
            raise KeyboardInterrupt

        def server_close(self):
            events.append("server.close")

    runtime = OrderedRuntime()
    stream = OrderedStateStream()
    server = OrderedServer()

    result = run_display_server(
        runtime_factory=lambda path: runtime,
        server_factory=lambda app, host, port, **kwargs: server,
        state_stream=stream,
    )

    assert result == 0

    assert events == [
        "runtime.start",
        "stream.start",
        "server.serve",
        "stream.stop",
        "stream.join",
        "server.close",
        "runtime.stop",
        "runtime.join",
    ]


def test_display_state_stream_uses_same_home_assistant_provider(
    monkeypatch,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()
    captured = {}

    class FakeProvider:
        pass

    provider = FakeProvider()

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["consumer_provider"] = provider
            captured["observation_adapter"] = observation_adapter
            captured["observation_sink"] = observation_sink

    class FakeStateStream:
        def __init__(
            self,
            *,
            base_url,
            token,
            consumer,
        ):
            captured["stream_base_url"] = base_url
            captured["stream_token"] = token
            captured["stream_consumer"] = consumer

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://192.0.2.2:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: provider,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
        raising=False,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
        raising=False,
    )

    def runtime_factory(path):
        return runtime

    def server_factory(app, host, port, **kwargs):
        captured["app_provider"] = (
            app._home_provider
        )
        return server

    result = run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
    )

    assert result == 0

    assert captured["app_provider"] is provider
    assert (
        captured["consumer_provider"]
        is provider
    )

    assert captured["stream_base_url"] == (
        "http://192.0.2.2:8123"
    )
    assert captured["stream_token"] == (
        "secret-token"
    )


def test_display_does_not_create_state_stream_without_ha_credentials(
    monkeypatch,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()

    class FakeProvider:
        pass

    provider = FakeProvider()

    created = {
        "consumer": False,
        "stream": False,
    }

    class FakeConsumer:
        def __init__(self, provider):
            created["consumer"] = True

    class FakeStateStream:
        def __init__(self, **kwargs):
            created["stream"] = True

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: provider,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: runtime,
        server_factory=lambda app, host, port, **kwargs: server,
    )

    assert created == {
        "consumer": False,
        "stream": False,
    }


def test_explicit_state_stream_prevents_automatic_stream_creation(
    monkeypatch,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()

    class FakeProvider:
        pass

    class InjectedStateStream:
        def __init__(self):
            self.started = False
            self.stopped = False
            self.joined = False

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def join(self, timeout=None):
            self.joined = True

    injected_stream = InjectedStateStream()

    automatic_stream_created = {
        "value": False,
    }

    class AutomaticStateStream:
        def __init__(self, **kwargs):
            automatic_stream_created[
                "value"
            ] = True

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://192.0.2.2:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        AutomaticStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: runtime,
        server_factory=lambda app, host, port, **kwargs: server,
        state_stream=injected_stream,
    )

    assert automatic_stream_created[
        "value"
    ] is False

    assert injected_stream.started is True
    assert injected_stream.stopped is True
    assert injected_stream.joined is True


def test_display_shares_home_status_notifier_with_provider_and_server(
    monkeypatch,
):
    runtime = FakeRuntimeHost()
    server = FakeHttpServer()

    captured = {}

    class FakeNotifier:
        pass

    notifier = FakeNotifier()

    class FakeProvider:
        pass

    provider = FakeProvider()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeStatusChangeNotifier",
        lambda: notifier,
        raising=False,
    )

    def create_provider(**kwargs):
        captured["provider_notifier"] = (
            kwargs.get("change_notifier")
        )
        return provider

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        create_provider,
    )

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        captured["server_notifier"] = (
            kwargs.get(
                "home_status_notifier"
            )
        )
        return server

    result = run_display_server(
        runtime_factory=lambda path: runtime,
        server_factory=server_factory,
    )

    assert result == 0

    assert (
        captured["provider_notifier"]
        is notifier
    )

    assert (
        captured["server_notifier"]
        is notifier
    )


def test_main_accepts_calendar_config_file(
    monkeypatch,
    tmp_path,
):
    from src.smartscreen_display import application

    captured = {}
    calendar_file = tmp_path / "calendar.json"

    def fake_run_display_server(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_display_server",
        fake_run_display_server,
    )

    result = application.main(
        [
            "--calendar-config-file",
            str(calendar_file),
        ]
    )

    assert result == 0
    assert (
        captured["calendar_config_file"]
        == calendar_file
    )

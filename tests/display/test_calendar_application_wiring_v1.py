import json

from src.smartscreen_display.application import (
    run_display_server,
)


class FakeRuntime:
    def start_background(self):
        pass

    def stop(self):
        pass

    def join(self, timeout=None):
        pass

    def stop_background(self):
        pass

    def snapshot(self):
        return {}


class FakeServer:
    def serve_forever(self):
        pass

    def shutdown(self):
        pass

    def server_close(self):
        pass


def test_run_display_server_wires_caldav_without_eventkit(tmp_path, monkeypatch):
    import src.smartscreen_display.application as module

    monkeypatch.delenv("SMARTSCREEN_HA_URL", raising=False)
    monkeypatch.delenv("SMARTSCREEN_HA_TOKEN", raising=False)
    def forbidden(**kwargs):
        raise AssertionError("EventKit must not start for CalDAV")
    monkeypatch.setattr(module, "EventKitSubprocessRunner", forbidden)
    calendar = tmp_path / "calendar.json"
    calendar.write_text(json.dumps({"enabled": True, "provider": "caldav"}))
    captured = {}
    def server_factory(app, **kwargs):
        captured["app"] = app
        return FakeServer()
    run_display_server(
        runtime_factory=lambda _: FakeRuntime(), server_factory=server_factory,
        calendar_config_file=calendar, **_write_required_files(tmp_path),
    )
    service = captured["app"]._calendar_event_service
    assert isinstance(service._source, module.BackgroundCalendarSource)
    assert isinstance(service._source._source, module.CalDAVCalendarSource)
    assert service._calendar_id is None
    assert not service._source._source._cache


def _write_required_files(tmp_path):
    home = tmp_path / "home.json"
    home.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "locations": [],
            }
        ),
        encoding="utf-8",
    )

    devices = tmp_path / "devices.json"
    devices.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "devices": [],
            }
        ),
        encoding="utf-8",
    )

    platform_entities = (
        tmp_path / "platform_entities.json"
    )
    platform_entities.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entities": [],
            }
        ),
        encoding="utf-8",
    )

    household_actions = (
        tmp_path / "household_actions.json"
    )
    household_actions.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "actions": [],
            }
        ),
        encoding="utf-8",
    )

    return {
        "location_config_file": home,
        "device_data_file": devices,
        "platform_entities_file": platform_entities,
        "household_actions_file": household_actions,
    }


def test_nas_argument_migration_preserves_data_paths_and_live_home_provider(tmp_path, monkeypatch):
    from pathlib import Path
    from src.smartscreen_display import application as module

    # Match the actual container arguments, not the image CMD: production
    # omits --home-file so that the live HA provider remains available.
    args = module.build_parser().parse_args([
        "--config", "/app/config/runtime.yaml", "--host", "0.0.0.0", "--port", "8080",
        "--photo-dir", "/persistent/photos", "--todo-file", "/persistent/todos/todos.json",
        "--home-entities-file", "/app/config/home_entities.json",
        "--calendar-config-file", "/run/smartscreen/calendar.json",
    ])
    assert args.home_file is None
    assert args.photo_dir == Path("/persistent/photos")
    assert args.todo_file == Path("/persistent/todos/todos.json")
    assert args.calendar_config_file == Path("/run/smartscreen/calendar.json")
    monkeypatch.delenv("SMARTSCREEN_HA_URL", raising=False)
    monkeypatch.delenv("SMARTSCREEN_HA_TOKEN", raising=False)
    provider, captured = object(), {}
    def create_provider(**kwargs):
        captured["entities_file"] = kwargs["entities_file"]
        return provider
    monkeypatch.setattr(module, "create_home_assistant_provider", create_provider)
    class Stream:
        def start(self): pass
        def stop(self): pass
        def join(self, **kwargs): pass
    def server_factory(app, **kwargs):
        captured["app"] = app
        return FakeServer()
    disabled = tmp_path / "calendar.json"
    disabled.write_text(json.dumps({"enabled": False}))
    run_display_server(
        runtime_factory=lambda _: FakeRuntime(), server_factory=server_factory,
        config_path=args.config, bind_host=args.host, port=args.port,
        photo_dir=args.photo_dir, todo_file=args.todo_file, home_file=args.home_file,
        home_entities_file=args.home_entities_file, calendar_config_file=disabled,
        state_stream=Stream(), **_write_required_files(tmp_path),
    )
    assert captured["app"]._home_provider is provider
    assert captured["app"]._photo_dir == args.photo_dir
    assert captured["app"]._todo_file == args.todo_file
    assert captured["entities_file"] == args.home_entities_file


def test_run_display_server_wires_enabled_calendar(
    tmp_path,
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
    bridge = tmp_path / "eventkit_bridge"
    bridge.write_text("", encoding="utf-8")

    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": True,
                "provider": "eventkit",
                "calendar_id": "family-calendar",
                "bridge_executable": str(bridge),
            }
        ),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(app, host, port, **kwargs):
        captured["app"] = app
        return FakeServer()

    kwargs = _write_required_files(tmp_path)

    run_display_server(
        runtime_factory=lambda config_path: FakeRuntime(),
        server_factory=server_factory,
        calendar_config_file=calendar,
        **kwargs,
    )

    app = captured["app"]

    service = app._calendar_event_service

    assert service is not None
    assert service._calendar_id == "family-calendar"

    source = service._source

    assert (
        source._runner._executable
        == bridge
    )


def test_run_display_server_wires_disabled_calendar_as_none(
    tmp_path,
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
    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": False,
            }
        ),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(app, host, port, **kwargs):
        captured["app"] = app
        return FakeServer()

    kwargs = _write_required_files(tmp_path)

    run_display_server(
        runtime_factory=lambda config_path: FakeRuntime(),
        server_factory=server_factory,
        calendar_config_file=calendar,
        **kwargs,
    )

    assert (
        captured["app"]._calendar_event_service
        is None
    )


def test_run_display_server_wires_all_calendars(
    tmp_path,
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

    bridge = tmp_path / "eventkit_bridge"
    bridge.write_text("", encoding="utf-8")

    calendar = tmp_path / "calendar.json"
    calendar.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": True,
                "provider": "eventkit",
                "bridge_executable": str(bridge),
            }
        ),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(app, host, port, **kwargs):
        captured["app"] = app
        return FakeServer()

    kwargs = _write_required_files(tmp_path)

    run_display_server(
        runtime_factory=lambda config_path: FakeRuntime(),
        server_factory=server_factory,
        calendar_config_file=calendar,
        **kwargs,
    )

    service = captured["app"]._calendar_event_service

    assert service is not None
    assert service._calendar_id is None
    assert service._source._runner._executable == bridge


def test_background_calendar_lifecycle_is_nonblocking_and_scoped(tmp_path, monkeypatch):
    import src.smartscreen_display.application as module
    calls = []
    class Background:
        def __init__(self, source, *, config):
            assert isinstance(source, module.CalDAVCalendarSource)
        def start(self):
            calls.append('calendar-start')
        def stop(self):
            calls.append('calendar-stop')
        def join(self, timeout):
            assert timeout == 1
            calls.append('calendar-join')
    class Server(FakeServer):
        def serve_forever(self):
            calls.append('serve')
    monkeypatch.setattr(module, 'BackgroundCalendarSource', Background)
    monkeypatch.delenv('SMARTSCREEN_HA_URL', raising=False)
    monkeypatch.delenv('SMARTSCREEN_HA_TOKEN', raising=False)
    calendar = tmp_path / 'calendar.json'
    calendar.write_text(json.dumps(dict(enabled=True, provider='caldav')))
    run_display_server(runtime_factory=lambda _: FakeRuntime(),
        server_factory=lambda *args, **kwargs: Server(), calendar_config_file=calendar,
        **_write_required_files(tmp_path))
    assert calls == ['calendar-start', 'serve', 'calendar-stop', 'calendar-join']

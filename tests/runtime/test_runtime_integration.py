from datetime import datetime, timezone

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


def create_integration_host():
    host = create_runtime_host_from_config(
        "config/runtime.test.yaml"
    )

    weather = host.engine.get_instance(
        "session-weather-main"
    )
    weather.set_provider(FakeWeatherProvider())

    return host


def test_runtime_integration_bootstraps_default_capabilities():
    host = create_integration_host()

    installed = {
        capability.capability_id
        for capability in host.engine.installed()
    }

    assert installed == {
        "com.smartscreen.capability.clock",
        "com.smartscreen.capability.weather",
    }


def test_runtime_integration_sessions_are_running():
    host = create_integration_host()

    snapshot = host.snapshot()

    states = {
        session["sessionId"]: session["state"]
        for session in snapshot["runtime"]["sessions"]
    }

    assert states["session-clock-main"] == "running"
    assert states["session-weather-main"] == "running"


def test_runtime_integration_tick_populates_weather():
    host = create_integration_host()

    results = host.engine.tick()

    assert results["session-weather-main"].success is True

    snapshot = host.snapshot()

    weather = snapshot["capabilities"][
        "session-weather-main"
    ]

    assert weather["condition"] == "sunny"
    assert weather["temperature"] == 26.0
    assert weather["humidity"] == 58


def test_runtime_integration_snapshot_contains_clock():
    host = create_integration_host()

    snapshot = host.snapshot()

    clock = snapshot["capabilities"][
        "session-clock-main"
    ]

    assert clock["timezone"] == "Asia/Shanghai"
    assert clock["timeFormat"] == "24h"
    assert "time" in clock
    assert "date" in clock


def test_runtime_integration_snapshot_contract():
    host = create_integration_host()

    host.engine.tick()
    snapshot = host.snapshot()

    assert snapshot["schemaVersion"] == "1.0"
    assert "generatedAt" in snapshot

    assert set(snapshot) == {
        "schemaVersion",
        "generatedAt",
        "runtime",
        "scheduler",
        "capabilities",
    }


def test_runtime_integration_scheduler_lifecycle():
    host = create_integration_host()

    host.start_background()

    assert host.running is True
    assert host.scheduler.background_running is True

    host.stop()
    host.join(timeout=1.0)

    assert host.running is False
    assert host.scheduler.background_running is False


def test_runtime_integration_shutdown_stops_all_sessions():
    host = create_integration_host()

    session_ids = [
        session.session_id
        for session in host.engine.sessions.list()
    ]

    for session_id in session_ids:
        host.engine.stop(session_id)

    assert host.engine.list_instances() == ()

    states = {
        session.session_id: session.state.value
        for session in host.engine.sessions.list()
    }

    assert states == {
        "session-clock-main": "stopped",
        "session-weather-main": "stopped",
    }

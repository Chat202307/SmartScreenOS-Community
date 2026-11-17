from datetime import datetime, timezone

from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


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


def create_host():
    engine = RuntimeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=1,
        start_time=100.0,
    )

    return RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )


def test_host_snapshot_contains_clock_data():
    host = create_host()

    capability = host.engine.install(
        "examples/capabilities/clock"
    )

    session = host.engine.start(
        capability.capability_id,
        session_id="session-clock-main",
        configuration={
            "timezone": "UTC",
            "timeFormat": "24h",
        },
    )

    snapshot = host.snapshot()

    data = snapshot["capabilities"][session.session_id]

    assert data["timezone"] == "UTC"
    assert data["timeFormat"] == "24h"
    assert "time" in data
    assert "date" in data

    host.engine.stop(session.session_id)


def test_host_snapshot_contains_weather_data():
    host = create_host()

    capability = host.engine.install(
        "examples/capabilities/weather"
    )

    session = host.engine.start(
        capability.capability_id,
        session_id="session-weather-main",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "celsius",
        },
    )

    weather = host.engine.get_instance(
        session.session_id
    )
    weather.set_provider(FakeWeatherProvider())
    weather.refresh()

    snapshot = host.snapshot()
    data = snapshot["capabilities"][session.session_id]

    assert data["location"] == "Dalian"
    assert data["condition"] == "sunny"
    assert data["temperature"] == 26.0
    assert data["humidity"] == 58

    host.engine.stop(session.session_id)


def test_host_snapshot_skips_capability_without_snapshot():
    host = create_host()

    class NoSnapshotCapability:
        pass

    host.engine._instances["session-no-snapshot"] = (
        NoSnapshotCapability()
    )

    snapshot = host.snapshot()

    assert "session-no-snapshot" not in snapshot["capabilities"]


def test_host_snapshot_reports_snapshot_that_raises():
    host = create_host()

    class FailingSnapshotCapability:
        def snapshot(self):
            raise RuntimeError("snapshot unavailable")

    host.engine._instances["session-failing"] = (
        FailingSnapshotCapability()
    )

    snapshot = host.snapshot()

    assert snapshot["capabilities"]["session-failing"] == {
        "status": "error",
        "error": "snapshot unavailable",
    }


def test_empty_host_snapshot_has_empty_capabilities():
    host = create_host()

    snapshot = host.snapshot()

    assert snapshot["capabilities"] == {}

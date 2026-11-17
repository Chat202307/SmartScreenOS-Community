from datetime import datetime, timezone

from src.smartscreen_runtime.runtime.engine import RuntimeEngine


class SuccessfulProvider:
    def fetch(self, location: str) -> dict:
        return {
            "condition": "sunny",
            "temperature": 25.0,
            "humidity": 50,
            "windSpeed": 10.0,
            "observedAt": datetime(
                2026,
                8,
                7,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        }


class FailingProvider:
    def fetch(self, location: str) -> dict:
        raise RuntimeError("provider unavailable")


def start_weather(
    engine: RuntimeEngine,
    session_id: str,
    provider,
):
    capability_id = "com.smartscreen.capability.weather"

    if capability_id not in engine.registry:
        engine.install("examples/capabilities/weather")

    session = engine.start(
        capability_id,
        session_id=session_id,
        configuration={
            "location": "Dalian",
            "refreshIntervalSeconds": 900,
        },
    )

    weather = engine.get_instance(session.session_id)
    weather.set_provider(provider)

    return session


def test_empty_runtime_snapshot():
    engine = RuntimeEngine()

    snapshot = engine.snapshot()

    assert snapshot["installed"] == []
    assert snapshot["sessions"] == []


def test_snapshot_contains_installed_capability():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    snapshot = engine.snapshot()

    assert snapshot["installed"] == [
        {
            "capabilityId": capability.capability_id,
            "name": capability.manifest.name,
            "version": capability.manifest.version,
        }
    ]


def test_snapshot_contains_running_session():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    snapshot = engine.snapshot()
    session_snapshot = snapshot["sessions"][0]

    assert session_snapshot["sessionId"] == session.session_id
    assert session_snapshot["capabilityId"] == capability.capability_id
    assert session_snapshot["state"] == "running"
    assert session_snapshot["tickHealth"] is None

    engine.stop(session.session_id)


def test_snapshot_contains_healthy_tick_state():
    engine = RuntimeEngine()

    session = start_weather(
        engine,
        "session-weather-001",
        SuccessfulProvider(),
    )

    engine.tick()

    snapshot = engine.snapshot()
    session_snapshot = snapshot["sessions"][0]

    assert session_snapshot["tickHealth"] == "healthy"
    assert session_snapshot["consecutiveFailures"] == 0
    assert session_snapshot["lastError"] is None

    engine.stop(session.session_id)


def test_snapshot_contains_failed_tick_state():
    engine = RuntimeEngine()

    session = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()

    snapshot = engine.snapshot()
    session_snapshot = snapshot["sessions"][0]

    assert session_snapshot["tickHealth"] == "degraded"
    assert session_snapshot["consecutiveFailures"] == 1
    assert session_snapshot["lastError"] == "provider unavailable"

    engine.stop(session.session_id)


def test_snapshot_contains_stopped_session():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )
    engine.stop(session.session_id)

    snapshot = engine.snapshot()
    session_snapshot = snapshot["sessions"][0]

    assert session_snapshot["state"] == "stopped"
    assert session_snapshot["tickHealth"] is None

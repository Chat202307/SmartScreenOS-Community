from datetime import datetime, timezone

import pytest

from src.smartscreen_runtime.runtime.engine import (
    CapabilityTickHealthNotFoundError,
    RuntimeEngine,
)


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
    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, location: str) -> dict:
        self.calls += 1
        raise RuntimeError(f"provider failure {self.calls}")


def start_weather(engine: RuntimeEngine, session_id: str, provider):
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

    return session, weather


def test_first_tick_failure_creates_health_record():
    engine = RuntimeEngine()
    session, _ = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()

    health = engine.get_tick_health(session.session_id)

    assert health.session_id == session.session_id
    assert health.consecutive_failures == 1
    assert isinstance(health.last_error, RuntimeError)
    assert health.last_success_at is None
    assert health.last_failure_at is not None

    engine.stop(session.session_id)


def test_repeated_failures_increment_counter():
    engine = RuntimeEngine()
    session, _ = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()
    engine.tick()
    engine.tick()

    health = engine.get_tick_health(session.session_id)

    assert health.consecutive_failures == 3
    assert "provider failure 3" in str(health.last_error)

    engine.stop(session.session_id)


def test_success_resets_failure_counter():
    engine = RuntimeEngine()
    failing_provider = FailingProvider()

    session, weather = start_weather(
        engine,
        "session-weather-001",
        failing_provider,
    )

    engine.tick()
    engine.tick()

    weather.set_provider(SuccessfulProvider())
    engine.tick()

    health = engine.get_tick_health(session.session_id)

    assert health.consecutive_failures == 0
    assert health.last_error is None
    assert health.last_success_at is not None
    assert health.last_failure_at is not None

    engine.stop(session.session_id)


def test_success_creates_healthy_record():
    engine = RuntimeEngine()
    session, _ = start_weather(
        engine,
        "session-weather-001",
        SuccessfulProvider(),
    )

    engine.tick()

    health = engine.get_tick_health(session.session_id)

    assert health.consecutive_failures == 0
    assert health.last_error is None
    assert health.last_success_at is not None
    assert health.last_failure_at is None

    engine.stop(session.session_id)


def test_unknown_tick_health_is_rejected():
    engine = RuntimeEngine()

    with pytest.raises(CapabilityTickHealthNotFoundError):
        engine.get_tick_health("unknown-session")


def test_stopping_session_removes_tick_health():
    engine = RuntimeEngine()
    session, _ = start_weather(
        engine,
        "session-weather-001",
        SuccessfulProvider(),
    )

    engine.tick()
    engine.stop(session.session_id)

    with pytest.raises(CapabilityTickHealthNotFoundError):
        engine.get_tick_health(session.session_id)

from datetime import datetime, timezone

import pytest

from src.smartscreen_runtime.runtime.engine import (
    CapabilityTickHealthNotFoundError,
    CapabilityTickHealthStatus,
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
    def fetch(self, location: str) -> dict:
        raise RuntimeError("provider unavailable")


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

    return session


def test_successful_tick_is_healthy():
    engine = RuntimeEngine()
    session = start_weather(
        engine,
        "session-weather-001",
        SuccessfulProvider(),
    )

    engine.tick()

    assert (
        engine.get_tick_health_status(session.session_id)
        is CapabilityTickHealthStatus.HEALTHY
    )

    engine.stop(session.session_id)


def test_first_failure_is_degraded():
    engine = RuntimeEngine()
    session = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()

    assert (
        engine.get_tick_health_status(session.session_id)
        is CapabilityTickHealthStatus.DEGRADED
    )

    engine.stop(session.session_id)


def test_second_failure_is_degraded():
    engine = RuntimeEngine()
    session = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()
    engine.tick()

    assert (
        engine.get_tick_health_status(session.session_id)
        is CapabilityTickHealthStatus.DEGRADED
    )

    engine.stop(session.session_id)


def test_third_failure_is_unhealthy():
    engine = RuntimeEngine()
    session = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()
    engine.tick()
    engine.tick()

    assert (
        engine.get_tick_health_status(session.session_id)
        is CapabilityTickHealthStatus.UNHEALTHY
    )

    engine.stop(session.session_id)


def test_recovery_returns_to_healthy():
    engine = RuntimeEngine()

    session = start_weather(
        engine,
        "session-weather-001",
        FailingProvider(),
    )

    engine.tick()
    engine.tick()
    engine.tick()

    weather = engine.get_instance(session.session_id)
    weather.set_provider(SuccessfulProvider())

    engine.tick()

    assert (
        engine.get_tick_health_status(session.session_id)
        is CapabilityTickHealthStatus.HEALTHY
    )

    engine.stop(session.session_id)


def test_unknown_health_status_is_rejected():
    engine = RuntimeEngine()

    with pytest.raises(CapabilityTickHealthNotFoundError):
        engine.get_tick_health_status("unknown-session")

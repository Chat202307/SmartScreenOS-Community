from datetime import datetime, timezone

from src.smartscreen_runtime.runtime.engine import (
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


def test_empty_health_summary():
    engine = RuntimeEngine()

    assert engine.get_tick_health_summary() == {}


def test_summary_contains_healthy_session():
    engine = RuntimeEngine()

    session = start_weather(
        engine,
        "session-weather-001",
        SuccessfulProvider(),
    )

    engine.tick()

    assert engine.get_tick_health_summary() == {
        session.session_id: CapabilityTickHealthStatus.HEALTHY,
    }

    engine.stop(session.session_id)


def test_summary_contains_multiple_health_levels():
    engine = RuntimeEngine()

    healthy_session = start_weather(
        engine,
        "session-weather-healthy",
        SuccessfulProvider(),
    )
    degraded_session = start_weather(
        engine,
        "session-weather-degraded",
        FailingProvider(),
    )
    unhealthy_session = start_weather(
        engine,
        "session-weather-unhealthy",
        FailingProvider(),
    )

    engine.tick()

    degraded_weather = engine.get_instance(
        degraded_session.session_id
    )
    degraded_weather.set_provider(SuccessfulProvider())

    engine.tick()
    engine.tick()

    summary = engine.get_tick_health_summary()

    assert (
        summary[healthy_session.session_id]
        is CapabilityTickHealthStatus.HEALTHY
    )
    assert (
        summary[degraded_session.session_id]
        is CapabilityTickHealthStatus.HEALTHY
    )
    assert (
        summary[unhealthy_session.session_id]
        is CapabilityTickHealthStatus.UNHEALTHY
    )

    engine.stop(healthy_session.session_id)
    engine.stop(degraded_session.session_id)
    engine.stop(unhealthy_session.session_id)


def test_summary_removes_stopped_session():
    engine = RuntimeEngine()

    session = start_weather(
        engine,
        "session-weather-001",
        SuccessfulProvider(),
    )

    engine.tick()
    engine.stop(session.session_id)

    assert session.session_id not in engine.get_tick_health_summary()


def test_summary_does_not_include_sessions_without_tick_health():
    engine = RuntimeEngine()

    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    assert session.session_id not in engine.get_tick_health_summary()

    engine.stop(session.session_id)

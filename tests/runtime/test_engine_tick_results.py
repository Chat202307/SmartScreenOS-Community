from dataclasses import dataclass
from datetime import datetime, timezone

from src.smartscreen_runtime.runtime.engine import RuntimeEngine


class SuccessfulProvider:
    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, location: str) -> dict:
        self.calls += 1
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

    return session, weather


def test_tick_returns_success_result():
    engine = RuntimeEngine()
    provider = SuccessfulProvider()

    session, weather = start_weather(
        engine,
        "session-weather-001",
        provider,
    )

    results = engine.tick()
    result = results[session.session_id]

    assert result.session_id == session.session_id
    assert result.success is True
    assert result.error is None
    assert provider.calls == 1
    assert weather.snapshot()["temperature"] == 25.0

    engine.stop(session.session_id)


def test_tick_isolates_failure_between_sessions():
    engine = RuntimeEngine()

    failing_provider = FailingProvider()
    successful_provider = SuccessfulProvider()

    failed_session, _ = start_weather(
        engine,
        "session-weather-failed",
        failing_provider,
    )
    successful_session, successful_weather = start_weather(
        engine,
        "session-weather-success",
        successful_provider,
    )

    results = engine.tick()

    failed_result = results[failed_session.session_id]
    successful_result = results[successful_session.session_id]

    assert failed_result.success is False
    assert isinstance(failed_result.error, RuntimeError)
    assert "provider unavailable" in str(failed_result.error)

    assert successful_result.success is True
    assert successful_result.error is None
    assert successful_provider.calls == 1
    assert successful_weather.snapshot()["temperature"] == 25.0

    engine.stop(failed_session.session_id)
    engine.stop(successful_session.session_id)


def test_tick_does_not_include_stopped_sessions():
    engine = RuntimeEngine()
    provider = SuccessfulProvider()

    session, _ = start_weather(
        engine,
        "session-weather-001",
        provider,
    )

    engine.stop(session.session_id)

    results = engine.tick()

    assert session.session_id not in results
    assert provider.calls == 0


def test_tick_ignores_capability_without_tick_hook():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    results = engine.tick()

    assert session.session_id not in results

    engine.stop(session.session_id)

from datetime import datetime, timezone

import pytest

from src.smartscreen_runtime.runtime.capability_api import CapabilityContext
from src.smartscreen_runtime.runtime.engine import RuntimeEngine


class FakeWeatherProvider:
    def fetch(self, location: str) -> dict:
        assert location == "Dalian"

        return {
            "condition": "sunny",
            "temperature": 26.5,
            "humidity": 58,
            "windSpeed": 12.0,
            "observedAt": datetime(
                2026,
                8,
                7,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        }


def install_weather(engine: RuntimeEngine):
    return engine.install("examples/capabilities/weather")


def test_weather_returns_snapshot():
    engine = RuntimeEngine()
    capability = install_weather(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
    )

    weather = engine.get_instance(session.session_id)
    weather.set_provider(FakeWeatherProvider())

    snapshot = weather.refresh()

    assert snapshot["location"] == "Dalian"
    assert snapshot["condition"] == "sunny"
    assert snapshot["temperature"] == 26.5
    assert snapshot["temperatureUnit"] == "celsius"
    assert snapshot["humidity"] == 58
    assert snapshot["windSpeed"] == 12.0
    assert snapshot["windSpeedUnit"] == "km/h"
    assert snapshot["observedAt"] == "2026-08-07T08:00:00+00:00"

    engine.stop(session.session_id)


def test_weather_snapshot_returns_latest_data():
    engine = RuntimeEngine()
    capability = install_weather(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
    )

    weather = engine.get_instance(session.session_id)
    weather.set_provider(FakeWeatherProvider())
    refreshed = weather.refresh()

    assert weather.snapshot() == refreshed

    engine.stop(session.session_id)


def test_weather_requires_refresh_before_snapshot():
    engine = RuntimeEngine()
    capability = install_weather(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
    )

    weather = engine.get_instance(session.session_id)

    with pytest.raises(RuntimeError, match="no weather data"):
        weather.snapshot()

    engine.stop(session.session_id)


def test_weather_rejects_missing_location():
    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={},
        logger=__import__("logging").getLogger("test.weather"),
    )

    from examples.capabilities.weather.capability import WeatherCapability

    with pytest.raises(ValueError, match="location"):
        WeatherCapability().start(context)


def test_weather_rejects_invalid_temperature_unit():
    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "kelvin",
        },
        logger=__import__("logging").getLogger("test.weather"),
    )

    from examples.capabilities.weather.capability import WeatherCapability

    with pytest.raises(ValueError, match="temperature"):
        WeatherCapability().start(context)


def test_weather_requires_running_state():
    engine = RuntimeEngine()
    capability = install_weather(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
    )

    weather = engine.get_instance(session.session_id)
    engine.stop(session.session_id)

    with pytest.raises(RuntimeError, match="not running"):
        weather.refresh()

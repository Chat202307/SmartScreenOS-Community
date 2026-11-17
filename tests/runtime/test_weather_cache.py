from datetime import datetime, timedelta, timezone

import logging

from examples.capabilities.weather.capability import WeatherCapability
from src.smartscreen_runtime.runtime.capability_api import CapabilityContext


class FakeWeatherProvider:
    def fetch(self, location: str) -> dict:
        return {
            "condition": "sunny",
            "temperature": 26.0,
            "humidity": 50,
            "windSpeed": 10.0,
            "observedAt": datetime(
                2026,
                8,
                7,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        }


def create_weather(
    refresh_interval_seconds: int = 900,
) -> WeatherCapability:
    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "celsius",
            "refreshIntervalSeconds": refresh_interval_seconds,
        },
        logger=logging.getLogger("test.weather"),
    )

    weather = WeatherCapability()
    weather.start(context)
    weather.set_provider(FakeWeatherProvider())
    return weather


def test_last_updated_is_none_before_refresh():
    weather = create_weather()

    assert weather.last_updated_at is None

    weather.stop()


def test_refresh_sets_last_updated_time():
    weather = create_weather()

    before = datetime.now(timezone.utc)
    weather.refresh()
    after = datetime.now(timezone.utc)

    assert weather.last_updated_at is not None
    assert before <= weather.last_updated_at <= after

    weather.stop()


def test_weather_is_stale_before_first_refresh():
    weather = create_weather()

    assert weather.is_stale() is True

    weather.stop()


def test_weather_is_fresh_within_refresh_interval():
    weather = create_weather(refresh_interval_seconds=900)
    weather.refresh()

    now = weather.last_updated_at + timedelta(seconds=899)

    assert weather.is_stale(now=now) is False

    weather.stop()


def test_weather_is_stale_at_refresh_interval_boundary():
    weather = create_weather(refresh_interval_seconds=900)
    weather.refresh()

    now = weather.last_updated_at + timedelta(seconds=900)

    assert weather.is_stale(now=now) is True

    weather.stop()


def test_invalid_refresh_interval_is_rejected():
    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "celsius",
            "refreshIntervalSeconds": 0,
        },
        logger=logging.getLogger("test.weather"),
    )

    weather = WeatherCapability()

    try:
        weather.start(context)
    except ValueError as exc:
        assert "refresh interval" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")

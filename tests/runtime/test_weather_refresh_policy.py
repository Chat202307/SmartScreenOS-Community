from datetime import datetime, timedelta, timezone
import logging

from examples.capabilities.weather.capability import WeatherCapability
from src.smartscreen_runtime.runtime.capability_api import CapabilityContext


class CountingWeatherProvider:
    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, location: str) -> dict:
        self.calls += 1

        return {
            "condition": "sunny",
            "temperature": 20.0 + self.calls,
            "humidity": 50,
            "windSpeed": 10.0,
            "observedAt": datetime(
                2026,
                8,
                7,
                8,
                self.calls,
                tzinfo=timezone.utc,
            ),
        }


def create_weather():
    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "celsius",
            "refreshIntervalSeconds": 900,
        },
        logger=logging.getLogger("test.weather"),
    )

    provider = CountingWeatherProvider()
    weather = WeatherCapability()
    weather.start(context)
    weather.set_provider(provider)

    return weather, provider


def test_refresh_if_stale_refreshes_without_cache():
    weather, provider = create_weather()

    snapshot = weather.refresh_if_stale()

    assert provider.calls == 1
    assert snapshot["temperature"] == 21.0

    weather.stop()


def test_refresh_if_stale_uses_fresh_cache():
    weather, provider = create_weather()

    first = weather.refresh()
    now = weather.last_updated_at + timedelta(seconds=899)

    second = weather.refresh_if_stale(now=now)

    assert provider.calls == 1
    assert second is first

    weather.stop()


def test_refresh_if_stale_refreshes_expired_cache():
    weather, provider = create_weather()

    first = weather.refresh()
    now = weather.last_updated_at + timedelta(seconds=900)

    second = weather.refresh_if_stale(now=now)

    assert provider.calls == 2
    assert second is not first
    assert second["temperature"] == 22.0

    weather.stop()


def test_refresh_if_stale_requires_running_state():
    weather, provider = create_weather()
    weather.stop()

    try:
        weather.refresh_if_stale()
    except RuntimeError as exc:
        assert "not running" in str(exc).lower()
    else:
        raise AssertionError("Expected RuntimeError")

    assert provider.calls == 0

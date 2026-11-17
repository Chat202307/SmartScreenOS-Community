import logging

from examples.capabilities.weather.capability import WeatherCapability
from examples.capabilities.weather.qweather_provider import QWeatherProvider
from src.smartscreen_runtime.runtime.capability_api import CapabilityContext


def test_weather_automatically_creates_configured_provider(monkeypatch):
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_API_HOST",
        "abc1234xyz.def.qweatherapi.com",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_API_KEY",
        "test-api-key",
    )

    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={
            "location": "101010100",
            "temperatureUnit": "celsius",
            "provider": "qweather",
            "language": "zh",
        },
        logger=logging.getLogger("test.weather"),
    )

    weather = WeatherCapability()
    weather.start(context)

    assert isinstance(weather.provider, QWeatherProvider)

    weather.stop()


def test_weather_without_provider_configuration_stays_unbound():
    context = CapabilityContext(
        session_id="session-weather-001",
        capability_id="com.smartscreen.capability.weather",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "celsius",
        },
        logger=logging.getLogger("test.weather"),
    )

    weather = WeatherCapability()
    weather.start(context)

    assert weather.provider is None

    weather.stop()

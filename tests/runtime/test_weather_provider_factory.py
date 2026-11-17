import os

import pytest

from examples.capabilities.weather.provider_factory import (
    WeatherProviderConfigurationError,
    create_weather_provider,
)
from examples.capabilities.weather.qweather_provider import QWeatherProvider


def test_create_qweather_provider_from_environment():
    environment = {
        "SMARTSCREEN_QWEATHER_API_HOST": (
            "abc1234xyz.def.qweatherapi.com"
        ),
        "SMARTSCREEN_QWEATHER_API_KEY": "test-api-key",
    }

    provider = create_weather_provider(
        {
            "provider": "qweather",
            "language": "zh",
        },
        environ=environment,
    )

    assert isinstance(provider, QWeatherProvider)


def test_missing_qweather_api_host_is_rejected():
    environment = {
        "SMARTSCREEN_QWEATHER_API_KEY": "test-api-key",
    }

    with pytest.raises(
        WeatherProviderConfigurationError,
        match="SMARTSCREEN_QWEATHER_API_HOST",
    ):
        create_weather_provider(
            {"provider": "qweather"},
            environ=environment,
        )


def test_missing_qweather_api_key_is_rejected():
    environment = {
        "SMARTSCREEN_QWEATHER_API_HOST": (
            "abc1234xyz.def.qweatherapi.com"
        ),
    }

    with pytest.raises(
        WeatherProviderConfigurationError,
        match="SMARTSCREEN_QWEATHER_API_KEY",
    ):
        create_weather_provider(
            {"provider": "qweather"},
            environ=environment,
        )


def test_unknown_weather_provider_is_rejected():
    with pytest.raises(
        WeatherProviderConfigurationError,
        match="unsupported",
    ):
        create_weather_provider(
            {"provider": "unknown"},
            environ={},
        )


def test_missing_provider_returns_none():
    assert create_weather_provider({}, environ={}) is None


def test_factory_uses_process_environment_by_default(monkeypatch):
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_API_HOST",
        "abc1234xyz.def.qweatherapi.com",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_API_KEY",
        "test-api-key",
    )

    provider = create_weather_provider(
        {"provider": "qweather"}
    )

    assert isinstance(provider, QWeatherProvider)

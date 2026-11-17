from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from .qweather_provider import QWeatherProvider


class WeatherProviderConfigurationError(ValueError):
    """Raised when weather provider configuration is invalid."""


def create_weather_provider(
    configuration: Mapping[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
):
    """Create a configured weather provider.

    When no provider is configured, return None so tests or callers can
    inject a provider manually.
    """

    provider_name = configuration.get("provider")

    if provider_name is None:
        return None

    if not isinstance(provider_name, str) or not provider_name.strip():
        raise WeatherProviderConfigurationError(
            "Weather provider must be a non-empty string."
        )

    normalized_name = provider_name.strip().lower()

    if normalized_name != "qweather":
        raise WeatherProviderConfigurationError(
            f"unsupported weather provider: {provider_name}"
        )

    environment = os.environ if environ is None else environ

    api_host = environment.get(
        "SMARTSCREEN_QWEATHER_API_HOST",
        "",
    ).strip()
    api_key = environment.get(
        "SMARTSCREEN_QWEATHER_API_KEY",
        "",
    ).strip()

    if not api_host:
        raise WeatherProviderConfigurationError(
            "SMARTSCREEN_QWEATHER_API_HOST is required "
            "for the qweather provider."
        )

    if not api_key:
        raise WeatherProviderConfigurationError(
            "SMARTSCREEN_QWEATHER_API_KEY is required "
            "for the qweather provider."
        )

    language = configuration.get("language", "zh")
    timeout = configuration.get("timeout", 10.0)

    return QWeatherProvider(
        api_host=api_host,
        api_key=api_key,
        language=language,
        timeout=timeout,
    )

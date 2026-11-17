from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, TypedDict

from src.smartscreen_runtime.runtime.capability_api import (
    Capability,
    CapabilityContext,
)

from examples.capabilities.weather.provider_factory import create_weather_provider


class WeatherProvider(Protocol):
    def fetch(self, location: str) -> dict[str, Any]:
        """Return current weather data for a location."""


class WeatherSnapshot(TypedDict):
    location: str
    condition: str
    temperature: float
    temperatureUnit: str
    humidity: int
    windSpeed: float
    windSpeedUnit: str
    observedAt: str


class WeatherProviderNotConfiguredError(RuntimeError):
    """Raised when refresh is called without a weather provider."""


class WeatherCapability(Capability):
    """Provide current weather observations through a pluggable provider."""

    SUPPORTED_TEMPERATURE_UNITS = frozenset({"celsius", "fahrenheit"})

    def __init__(self) -> None:
        self.started = False
        self.context: CapabilityContext | None = None
        self._location = ""
        self._temperature_unit = "celsius"
        self._provider: WeatherProvider | None = None
        self._snapshot: WeatherSnapshot | None = None
        self._last_updated_at: datetime | None = None
        self._refresh_interval_seconds = 900

    @property
    def provider(self) -> WeatherProvider | None:
        return self._provider

    @property
    def last_updated_at(self) -> datetime | None:
        return self._last_updated_at

    def start(self, context: CapabilityContext) -> None:
        location = context.configuration.get("location")
        temperature_unit = context.configuration.get(
            "temperatureUnit",
            "celsius",
        )

        if not isinstance(location, str) or not location.strip():
            raise ValueError(
                "Weather location must be a non-empty string."
            )

        if temperature_unit not in self.SUPPORTED_TEMPERATURE_UNITS:
            raise ValueError(
                "Weather temperature unit must be "
                "'celsius' or 'fahrenheit'."
            )

        refresh_interval_seconds = context.configuration.get(
            "refreshIntervalSeconds",
            900,
        )

        if (
            not isinstance(refresh_interval_seconds, int)
            or isinstance(refresh_interval_seconds, bool)
            or refresh_interval_seconds <= 0
        ):
            raise ValueError(
                "Weather refresh interval must be a positive integer."
            )

        provider = create_weather_provider(
            context.configuration
        )

        self.context = context
        self._location = location.strip()
        self._temperature_unit = temperature_unit
        self._refresh_interval_seconds = refresh_interval_seconds
        self._provider = provider
        self._snapshot = None
        self._last_updated_at = None
        self.started = True

    def stop(self) -> None:
        self.started = False

    def set_provider(self, provider: WeatherProvider) -> None:
        self._provider = provider

    def refresh(self) -> WeatherSnapshot:
        self._require_running()

        if self._provider is None:
            raise WeatherProviderNotConfiguredError(
                "Weather provider is not configured."
            )

        data = self._provider.fetch(self._location)

        observed_at = data["observedAt"]
        if not isinstance(observed_at, datetime):
            raise TypeError(
                "Weather observedAt must be a datetime instance."
            )

        snapshot: WeatherSnapshot = {
            "location": self._location,
            "condition": str(data["condition"]),
            "temperature": float(data["temperature"]),
            "temperatureUnit": self._temperature_unit,
            "humidity": int(data["humidity"]),
            "windSpeed": float(data["windSpeed"]),
            "windSpeedUnit": "km/h",
            "observedAt": observed_at.isoformat(),
        }

        self._snapshot = snapshot
        self._last_updated_at = datetime.now(timezone.utc)
        return snapshot

    def is_stale(
        self,
        *,
        now: datetime | None = None,
    ) -> bool:
        if self._last_updated_at is None:
            return True

        resolved_now = now or datetime.now(timezone.utc)

        if resolved_now.tzinfo is None:
            raise ValueError(
                "Weather stale-check time must be timezone-aware."
            )

        age_seconds = (
            resolved_now - self._last_updated_at
        ).total_seconds()

        return age_seconds >= self._refresh_interval_seconds

    def refresh_if_stale(
        self,
        *,
        now: datetime | None = None,
    ) -> WeatherSnapshot:
        self._require_running()

        if self._snapshot is None or self.is_stale(now=now):
            return self.refresh()

        return self._snapshot

    def snapshot(self) -> WeatherSnapshot:
        self._require_running()

        if self._snapshot is None:
            raise RuntimeError("There is no weather data available.")

        return self._snapshot

    def _require_running(self) -> None:
        if not self.started:
            raise RuntimeError("Weather capability is not running.")

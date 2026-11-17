from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from typing import Any

from src.smartscreen_platform.contracts import (
    Observation,
)


class HomeAssistantWeatherForecastAdapter:
    """Convert Home Assistant weather state/forecast into observations."""

    def __init__(
        self,
        *,
        entity_id: str,
        location_id: str,
        forecast_horizon_hours: float | None = None,
    ) -> None:
        self._entity_id = entity_id
        self._location_id = location_id
        self._forecast_horizon_hours = (
            forecast_horizon_hours
        )

    def convert_current(
        self,
        state: dict[str, Any],
    ) -> list[Observation]:
        if state.get("entity_id") != self._entity_id:
            return []

        attributes = state.get(
            "attributes",
            {},
        )

        if not isinstance(attributes, dict):
            return []

        observations = []

        condition = state.get(
            "state"
        )

        if (
            isinstance(condition, str)
            and condition
            and condition not in {
                "unknown",
                "unavailable",
            }
        ):
            observations.append(
                Observation.create(
                    parameter="weather_condition",
                    value=condition,
                    location_id=self._location_id,
                    provenance={
                        "provider": "home_assistant",
                        "entity_id": self._entity_id,
                        "source": "weather_current",
                    },
                )
            )

        wind_speed = attributes.get(
            "wind_speed"
        )
        wind_speed_unit = attributes.get(
            "wind_speed_unit"
        )

        if (
            wind_speed is not None
            and isinstance(
                wind_speed_unit,
                str,
            )
            and wind_speed_unit
        ):
            try:
                wind_speed_value = float(
                    wind_speed
                )
            except (TypeError, ValueError):
                wind_speed_value = None

            if (
                wind_speed_value is not None
                and wind_speed_value >= 0
            ):
                observations.append(
                    Observation.create(
                        parameter="wind_speed",
                        value=wind_speed_value,
                        unit=wind_speed_unit,
                        location_id=self._location_id,
                        provenance={
                            "provider": "home_assistant",
                            "entity_id": self._entity_id,
                            "source": "weather_current",
                        },
                    )
                )

        temperature = attributes.get(
            "temperature"
        )

        if temperature is not None:
            try:
                temperature_value = float(
                    temperature
                )
            except (TypeError, ValueError):
                temperature_value = None

            if temperature_value is not None:
                observations.append(
                    Observation.create(
                        parameter="temperature",
                        value=temperature_value,
                        unit="degC",
                        location_id=self._location_id,
                        provenance={
                            "provider": "home_assistant",
                            "entity_id": self._entity_id,
                            "source": "weather_current",
                        },
                    )
                )

        humidity = attributes.get(
            "humidity"
        )

        if humidity is not None:
            try:
                humidity_value = float(
                    humidity
                )
            except (TypeError, ValueError):
                humidity_value = None

            if humidity_value is not None:
                observations.append(
                    Observation.create(
                        parameter="humidity",
                        value=humidity_value,
                        unit="percent",
                        location_id=self._location_id,
                        provenance={
                            "provider": "home_assistant",
                            "entity_id": self._entity_id,
                            "source": "weather_current",
                        },
                    )
                )

        apparent_temperature = (
            self._calculate_apparent_temperature(
                attributes
            )
        )

        if apparent_temperature is not None:
            observations.append(
                Observation.create(
                    parameter="apparent_temperature",
                    value=apparent_temperature,
                    unit="degC",
                    location_id=self._location_id,
                    provenance={
                        "provider": "home_assistant",
                        "entity_id": self._entity_id,
                        "source": "weather_current",
                    },
                    metadata={
                        "model": (
                            "bom_apparent_temperature_v1"
                        ),
                    },
                )
            )

        return observations

    @staticmethod
    def _calculate_apparent_temperature(
        attributes,
    ):
        temperature = attributes.get(
            "temperature"
        )
        humidity = attributes.get(
            "humidity"
        )
        wind_speed = attributes.get(
            "wind_speed"
        )

        if (
            temperature is None
            or humidity is None
            or wind_speed is None
        ):
            return None

        try:
            temperature = float(
                temperature
            )
            humidity = float(
                humidity
            )
            wind_speed = float(
                wind_speed
            )
        except (TypeError, ValueError):
            return None

        if not (
            0.0 <= humidity <= 100.0
        ):
            return None

        if wind_speed < 0:
            return None

        wind_unit = attributes.get(
            "wind_speed_unit"
        )

        if wind_unit in {
            "km/h",
            "kmh",
            "kph",
        }:
            wind_speed_mps = (
                wind_speed / 3.6
            )
        elif wind_unit in {
            "m/s",
            "mps",
        }:
            wind_speed_mps = wind_speed
        else:
            return None

        vapour_pressure = (
            humidity
            / 100.0
            * 6.105
            * math.exp(
                (
                    17.27
                    * temperature
                )
                / (
                    237.7
                    + temperature
                )
            )
        )

        return (
            temperature
            + 0.33 * vapour_pressure
            - 0.70 * wind_speed_mps
            - 4.0
        )

    def convert_hourly_forecast(
        self,
        forecast: list[dict[str, Any]],
        *,
        now: str | datetime | None = None,
    ) -> list[Observation]:
        valid_items = [
            item
            for item in forecast
            if isinstance(item, dict)
        ]

        if self._forecast_horizon_hours is not None:
            reference_time = self._parse_datetime(
                now
            )

            if reference_time is None:
                reference_time = datetime.now(
                    timezone.utc
                )

            horizon_end = (
                reference_time
                + timedelta(
                    hours=self._forecast_horizon_hours
                )
            )

            valid_items = [
                item
                for item in valid_items
                if self._forecast_item_in_window(
                    item,
                    reference_time,
                    horizon_end,
                )
            ]

        if not valid_items:
            return []

        observations = []

        precipitation_items = []

        for item in valid_items:
            value = item.get(
                "precipitation"
            )

            if value is None:
                continue

            try:
                precipitation_value = float(
                    value
                )
            except (TypeError, ValueError):
                continue

            precipitation_items.append(
                (
                    precipitation_value,
                    item,
                )
            )

        if precipitation_items:
            (
                max_precipitation,
                precipitation_source,
            ) = max(
                precipitation_items,
                key=lambda pair: pair[0],
            )

            observations.append(
                Observation.create(
                    parameter="forecast_precipitation",
                    value=max_precipitation,
                    unit="mm",
                    location_id=self._location_id,
                    provenance={
                        "provider": "home_assistant",
                        "entity_id": self._entity_id,
                        "source": (
                            "weather_hourly_forecast"
                        ),
                        "forecast_datetime": (
                            precipitation_source.get(
                                "datetime"
                            )
                        ),
                    },
                )
            )

        condition_item = next(
            (
                item
                for item in valid_items
                if isinstance(
                    item.get("condition"),
                    str,
                )
                and item["condition"]
            ),
            None,
        )

        if condition_item is not None:
            observations.append(
                Observation.create(
                    parameter="forecast_condition",
                    value=condition_item[
                        "condition"
                    ],
                    location_id=self._location_id,
                    provenance={
                        "provider": "home_assistant",
                        "entity_id": self._entity_id,
                        "source": (
                            "weather_hourly_forecast"
                        ),
                        "forecast_datetime": (
                            condition_item.get(
                                "datetime"
                            )
                        ),
                    },
                )
            )

        return observations

    @staticmethod
    def _parse_datetime(
        value,
    ):
        if isinstance(value, datetime):
            parsed = value

        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    )
                )
            except ValueError:
                return None

        elif value is None:
            return None

        else:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    @classmethod
    def _forecast_item_in_window(
        cls,
        item,
        start,
        end,
    ):
        item_time = cls._parse_datetime(
            item.get("datetime")
        )

        if item_time is None:
            return False

        return (
            start
            <= item_time
            <= end
        )


class HomeAssistantWeatherForecastSource:
    """Poll Home Assistant hourly weather forecasts."""

    def __init__(
        self,
        *,
        base_url,
        token,
        entity_id,
        adapter,
        observation_accumulator,
        observation_sink,
        poll_interval_seconds=1800.0,
        retry_interval_seconds=30.0,
        client=None,
        clock=None,
    ):
        import threading

        from .home_assistant_client import (
            HomeAssistantClient,
        )

        self._entity_id = entity_id
        self._adapter = adapter
        self._observation_accumulator = (
            observation_accumulator
        )
        self._observation_sink = (
            observation_sink
        )
        self._poll_interval_seconds = float(
            poll_interval_seconds
        )
        self._retry_interval_seconds = float(
            retry_interval_seconds
        )
        self._clock = clock

        self._client = (
            client
            if client is not None
            else HomeAssistantClient(
                base_url,
                token,
            )
        )

        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        import threading

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_background,
            name=(
                "smartscreen-ha-weather-forecast"
            ),
            daemon=False,
        )

        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def join(self, timeout=None):
        if self._thread is None:
            return

        self._thread.join(
            timeout=timeout
        )

    def is_alive(self):
        return (
            self._thread is not None
            and self._thread.is_alive()
        )

    def _run_background(self):
        while not self._stop_event.is_set():
            wait_seconds = (
                self._poll_interval_seconds
            )

            try:
                self.run_once()
            except Exception:
                if self._stop_event.is_set():
                    return

                wait_seconds = (
                    self._retry_interval_seconds
                )

            if self._stop_event.wait(
                timeout=wait_seconds
            ):
                return

    def run_once(self):
        current_state = self._client.get_json(
            (
                "/api/states/"
                + self._entity_id
            )
        )

        current_observations = []

        if isinstance(current_state, dict):
            current_observations = (
                self._adapter.convert_current(
                    current_state
                )
            )

        forecast = []

        try:
            payload = self._client.post_json(
                (
                    "/api/services/weather/"
                    "get_forecasts?return_response"
                ),
                {
                    "entity_id": self._entity_id,
                    "type": "hourly",
                },
            )

            forecast = self._extract_forecast(
                payload
            )

        except Exception:
            if not current_observations:
                raise

        forecast_observations = (
            self._adapter.convert_hourly_forecast(
                forecast,
                now=(
                    self._clock()
                    if self._clock is not None
                    else None
                ),
            )
        )

        observations = (
            list(current_observations)
            + list(forecast_observations)
        )

        if not observations:
            return []

        first = observations[0]
        location_id = getattr(
            first,
            "location_id",
            None,
        )

        observations = (
            self._observation_accumulator.update(
                observations
            )
        )

        if location_id is not None:
            observations = (
                self._observation_accumulator.for_location(
                    location_id
                )
            )

        self._observation_sink.process(
            observations,
            location_id=location_id,
        )

        return observations

    def _extract_forecast(self, payload):
        if not isinstance(payload, dict):
            return []

        service_response = payload.get(
            "service_response"
        )

        if not isinstance(
            service_response,
            dict,
        ):
            return []

        entity_response = service_response.get(
            self._entity_id
        )

        if not isinstance(
            entity_response,
            dict,
        ):
            return []

        forecast = entity_response.get(
            "forecast",
            [],
        )

        if not isinstance(forecast, list):
            return []

        return forecast

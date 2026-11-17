from src.smartscreen_platform.contracts.state import (
    StatePatch,
)


class WeatherStatusCapability:
    """Project current weather observations into weather status."""

    name = "weather_status"

    managed_targets = (
        "weather_status",
    )

    _CURRENT_PARAMETERS = (
        "weather_condition",
        "temperature",
        "humidity",
        "apparent_temperature",
        "wind_speed",
    )

    def evaluate(
        self,
        interpretations,
        observations=None,
        knowledge=None,
    ):
        observations = [
            observation
            for observation in (
                observations or []
            )
            if (
                isinstance(
                    getattr(
                        observation,
                        "provenance",
                        None,
                    ),
                    dict,
                )
                and observation.provenance.get(
                    "source"
                )
                == "weather_current"
            )
        ]

        current = {
            item.parameter: item
            for item in observations
            if item.parameter
            in self._CURRENT_PARAMETERS
        }

        if not current:
            return []

        value = {}
        evidence_refs = []

        condition = current.get(
            "weather_condition"
        )

        if condition is not None:
            value["condition"] = (
                condition.value
            )
            evidence_refs.append(
                condition.observation_id
            )

        temperature = current.get(
            "temperature"
        )

        if temperature is not None:
            value["temperature"] = (
                temperature.value
            )
            if temperature.unit is not None:
                value["temperature_unit"] = (
                    temperature.unit
                )
            evidence_refs.append(
                temperature.observation_id
            )

        humidity = current.get(
            "humidity"
        )

        if humidity is not None:
            value["humidity"] = (
                humidity.value
            )
            if humidity.unit is not None:
                value["humidity_unit"] = (
                    humidity.unit
                )
            evidence_refs.append(
                humidity.observation_id
            )

        apparent_temperature = current.get(
            "apparent_temperature"
        )

        if apparent_temperature is not None:
            value[
                "apparent_temperature"
            ] = apparent_temperature.value

            if (
                apparent_temperature.unit
                is not None
            ):
                value[
                    "apparent_temperature_unit"
                ] = apparent_temperature.unit

            evidence_refs.append(
                apparent_temperature.observation_id
            )

        wind_speed = current.get(
            "wind_speed"
        )

        if wind_speed is not None:
            value["wind_speed"] = (
                wind_speed.value
            )
            if wind_speed.unit is not None:
                value["wind_speed_unit"] = (
                    wind_speed.unit
                )
            evidence_refs.append(
                wind_speed.observation_id
            )

        location_id = next(
            (
                item.location_id
                for item in current.values()
                if item.location_id is not None
            ),
            None,
        )

        return [
            StatePatch.create(
                capability=self.name,
                target="weather_status",
                value=value,
                confidence=0.9,
                ttl_seconds=3600,
                location_id=location_id,
                evidence_refs=evidence_refs,
                metadata={
                    "model": "weather_status_v1",
                },
            )
        ]

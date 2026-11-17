from src.smartscreen_platform.contracts.state import (
    StatePatch,
)


class WeatherAdviceCapability:
    """Project weather observations into practical advice."""

    name = "weather_advice"

    managed_targets = (
        "umbrella_advice",
        "clothing_advice",
    )

    def evaluate(
        self,
        interpretations,
        observations=None,
        knowledge=None,
    ):
        observations = list(
            observations or []
        )

        patches = []

        precipitation = self._find_observation(
            observations,
            "precipitation_probability",
        )

        if precipitation is not None:
            recommended = (
                float(precipitation.value) >= 50
            )

            patches.append(
                StatePatch.create(
                    capability=self.name,
                    target="umbrella_advice",
                    value={
                        "recommended": recommended,
                        "reason": (
                            "rain_forecast"
                            if recommended
                            else "low_rain_probability"
                        ),
                    },
                    confidence=0.9,
                    ttl_seconds=3600,
                    location_id=(
                        precipitation.location_id
                    ),
                    evidence_refs=[
                        precipitation.observation_id
                    ],
                    metadata={
                        "model": "weather_advice_v1",
                    },
                )
            )

        else:
            forecast_precipitation = (
                self._find_observation(
                    observations,
                    "forecast_precipitation",
                )
            )

            if forecast_precipitation is not None:
                recommended = (
                    float(
                        forecast_precipitation.value
                    )
                    > 0
                )

                patches.append(
                    StatePatch.create(
                        capability=self.name,
                        target="umbrella_advice",
                        value={
                            "recommended": recommended,
                            "reason": (
                                "forecast_precipitation"
                                if recommended
                                else (
                                    "no_forecast_precipitation"
                                )
                            ),
                        },
                        confidence=0.9,
                        ttl_seconds=3600,
                        location_id=(
                            forecast_precipitation.location_id
                        ),
                        evidence_refs=[
                            forecast_precipitation.observation_id
                        ],
                        metadata={
                            "model": "weather_advice_v1",
                        },
                    )
                )

        apparent_temperature = (
            self._find_observation(
                observations,
                "apparent_temperature",
            )
        )

        if apparent_temperature is not None:
            value = float(
                apparent_temperature.value
            )

            if value <= 10:
                level = "warm"
                reason = (
                    "cold_apparent_temperature"
                )
            elif value >= 28:
                level = "hot_weather"
                reason = (
                    "hot_apparent_temperature"
                )
            else:
                level = "light"
                reason = (
                    "mild_apparent_temperature"
                )

            patches.append(
                StatePatch.create(
                    capability=self.name,
                    target="clothing_advice",
                    value={
                        "level": level,
                        "reason": reason,
                    },
                    confidence=0.9,
                    ttl_seconds=3600,
                    location_id=(
                        apparent_temperature.location_id
                    ),
                    evidence_refs=[
                        apparent_temperature.observation_id
                    ],
                    metadata={
                        "model": "weather_advice_v1",
                    },
                )
            )

        return patches

    @staticmethod
    def _find_observation(
        observations,
        parameter,
    ):
        return next(
            (
                observation
                for observation in observations
                if observation.parameter
                == parameter
            ),
            None,
        )

from src.smartscreen_platform.contracts import (
    Observation,
)

from src.smartscreen_platform.capabilities.weather_status.capability import (
    WeatherStatusCapability,
)


def evaluate(observations):
    return WeatherStatusCapability().evaluate(
        interpretations=[],
        observations=observations,
    )


def observation(
    parameter,
    value,
    *,
    unit=None,
    location_id="outdoor",
):
    return Observation.create(
        parameter,
        value,
        unit=unit,
        location_id=location_id,
        provenance={
            "provider": "home_assistant",
            "entity_id": (
                "weather.demo_entity_065"
            ),
            "source": "weather_current",
        },
    )


def weather_status(patches):
    return next(
        item
        for item in patches
        if item.target == "weather_status"
    )


def test_weather_status_has_managed_target():
    capability = WeatherStatusCapability()

    assert capability.managed_targets == (
        "weather_status",
    )


def test_weather_status_projects_current_weather():
    patches = evaluate([
        observation(
            "weather_condition",
            "partlycloudy",
        ),
        observation(
            "temperature",
            25.4,
            unit="degC",
        ),
        observation(
            "humidity",
            80,
            unit="percent",
        ),
        observation(
            "apparent_temperature",
            27.4,
            unit="degC",
        ),
        observation(
            "wind_speed",
            13.3,
            unit="km/h",
        ),
    ])

    patch = weather_status(patches)

    assert patch.location_id == "outdoor"

    assert patch.value == {
        "condition": "partlycloudy",
        "temperature": 25.4,
        "temperature_unit": "degC",
        "humidity": 80,
        "humidity_unit": "percent",
        "apparent_temperature": 27.4,
        "apparent_temperature_unit": "degC",
        "wind_speed": 13.3,
        "wind_speed_unit": "km/h",
    }


def test_weather_status_allows_partial_current_weather():
    patches = evaluate([
        observation(
            "temperature",
            25.4,
            unit="degC",
        ),
        observation(
            "humidity",
            80,
            unit="percent",
        ),
    ])

    patch = weather_status(patches)

    assert patch.value == {
        "temperature": 25.4,
        "temperature_unit": "degC",
        "humidity": 80,
        "humidity_unit": "percent",
    }


def test_weather_status_requires_current_weather_evidence():
    patches = evaluate([
        observation(
            "forecast_condition",
            "rainy",
        ),
        observation(
            "forecast_precipitation",
            0.4,
            unit="mm",
        ),
    ])

    assert all(
        item.target != "weather_status"
        for item in patches
    )


def test_weather_status_is_location_scoped():
    patches = evaluate([
        observation(
            "weather_condition",
            "sunny",
            location_id="garden",
        ),
        observation(
            "temperature",
            28,
            unit="degC",
            location_id="garden",
        ),
    ])

    patch = weather_status(patches)

    assert patch.location_id == "garden"


def test_weather_status_preserves_evidence_refs():
    observations = [
        observation(
            "weather_condition",
            "cloudy",
        ),
        observation(
            "temperature",
            20,
            unit="degC",
        ),
        observation(
            "wind_speed",
            10,
            unit="km/h",
        ),
    ]

    patch = weather_status(
        evaluate(observations)
    )

    assert set(patch.evidence_refs) == {
        item.observation_id
        for item in observations
    }


def test_weather_status_ignores_non_weather_temperature():
    capability = WeatherStatusCapability()

    observations = [
        Observation.create(
            "temperature",
            31,
            unit="degC",
            location_id="living",
            provenance={
                "provider": "home_assistant",
                "entity_id": "sensor.living_temperature",
            },
        ),
        Observation.create(
            "humidity",
            75,
            unit="percent",
            location_id="living",
            provenance={
                "provider": "home_assistant",
                "entity_id": "sensor.living_humidity",
            },
        ),
    ]

    patches = capability.evaluate(
        interpretations=[],
        observations=observations,
    )

    assert patches == []


def test_weather_status_accepts_weather_current_provenance():
    capability = WeatherStatusCapability()

    observations = [
        Observation.create(
            "temperature",
            25.4,
            unit="degC",
            location_id="outdoor",
            provenance={
                "provider": "home_assistant",
                "entity_id": (
                    "weather.demo_entity_065"
                ),
                "source": "weather_current",
            },
        ),
    ]

    patches = capability.evaluate(
        interpretations=[],
        observations=observations,
    )

    assert len(patches) == 1
    assert patches[0].target == "weather_status"
    assert patches[0].location_id == "outdoor"

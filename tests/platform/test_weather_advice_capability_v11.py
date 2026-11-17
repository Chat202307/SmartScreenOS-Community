from src.smartscreen_platform.contracts import (
    Observation,
)

from src.smartscreen_platform.capabilities.weather_advice.capability import (
    WeatherAdviceCapability,
)


def evaluate(observations):
    return WeatherAdviceCapability().evaluate(
        interpretations=[],
        observations=observations,
    )


def test_rain_forecast_produces_umbrella_advice():
    patches = evaluate([
        Observation.create(
            "precipitation_probability",
            80,
            unit="percent",
            location_id="home",
        ),
    ])

    assert len(patches) == 1

    patch = patches[0]

    assert patch.target == "umbrella_advice"
    assert patch.location_id == "home"
    assert patch.value["recommended"] is True
    assert patch.value["reason"] == "rain_forecast"


def test_low_rain_probability_does_not_recommend_umbrella():
    patches = evaluate([
        Observation.create(
            "precipitation_probability",
            10,
            unit="percent",
            location_id="home",
        ),
    ])

    umbrella = [
        patch
        for patch in patches
        if patch.target == "umbrella_advice"
    ]

    assert len(umbrella) == 1
    assert umbrella[0].value["recommended"] is False


def test_missing_rain_probability_produces_no_umbrella_advice():
    patches = evaluate([
        Observation.create(
            "temperature",
            20,
            unit="degC",
            location_id="home",
        ),
    ])

    assert all(
        patch.target != "umbrella_advice"
        for patch in patches
    )


def test_cold_apparent_temperature_produces_warm_clothing_advice():
    patches = evaluate([
        Observation.create(
            "apparent_temperature",
            5,
            unit="degC",
            location_id="home",
        ),
    ])

    clothing = [
        patch
        for patch in patches
        if patch.target == "clothing_advice"
    ]

    assert len(clothing) == 1

    assert clothing[0].value == {
        "level": "warm",
        "reason": "cold_apparent_temperature",
    }


def test_mild_apparent_temperature_produces_light_clothing_advice():
    patches = evaluate([
        Observation.create(
            "apparent_temperature",
            21,
            unit="degC",
            location_id="home",
        ),
    ])

    clothing = [
        patch
        for patch in patches
        if patch.target == "clothing_advice"
    ]

    assert len(clothing) == 1
    assert clothing[0].value["level"] == "light"


def test_hot_apparent_temperature_produces_hot_weather_clothing_advice():
    patches = evaluate([
        Observation.create(
            "apparent_temperature",
            31,
            unit="degC",
            location_id="home",
        ),
    ])

    clothing = [
        patch
        for patch in patches
        if patch.target == "clothing_advice"
    ]

    assert len(clothing) == 1
    assert clothing[0].value["level"] == "hot_weather"


def test_missing_temperature_data_produces_no_clothing_advice():
    patches = evaluate([
        Observation.create(
            "precipitation_probability",
            50,
            unit="percent",
            location_id="home",
        ),
    ])

    assert all(
        patch.target != "clothing_advice"
        for patch in patches
    )


def test_weather_advice_is_location_scoped():
    patches = evaluate([
        Observation.create(
            "apparent_temperature",
            8,
            unit="degC",
            location_id="outdoor",
        ),
    ])

    assert patches[0].location_id == "outdoor"


def test_weather_advice_has_managed_targets():
    capability = WeatherAdviceCapability()

    assert capability.managed_targets == (
        "umbrella_advice",
        "clothing_advice",
    )


def test_forecast_precipitation_produces_umbrella_advice():
    capability = WeatherAdviceCapability()

    patches = capability.evaluate(
        interpretations=[],
        observations=[
            Observation.create(
                "forecast_precipitation",
                0.4,
                unit="mm",
                location_id="outdoor",
            )
        ],
    )

    patch = next(
        item
        for item in patches
        if item.target == "umbrella_advice"
    )

    assert patch.value == {
        "recommended": True,
        "reason": "forecast_precipitation",
    }
    assert patch.location_id == "outdoor"


def test_zero_forecast_precipitation_does_not_recommend_umbrella():
    capability = WeatherAdviceCapability()

    patches = capability.evaluate(
        interpretations=[],
        observations=[
            Observation.create(
                "forecast_precipitation",
                0.0,
                unit="mm",
                location_id="outdoor",
            )
        ],
    )

    patch = next(
        item
        for item in patches
        if item.target == "umbrella_advice"
    )

    assert patch.value == {
        "recommended": False,
        "reason": "no_forecast_precipitation",
    }


def test_precipitation_probability_remains_preferred_when_available():
    capability = WeatherAdviceCapability()

    patches = capability.evaluate(
        interpretations=[],
        observations=[
            Observation.create(
                "precipitation_probability",
                20,
                unit="percent",
                location_id="outdoor",
            ),
            Observation.create(
                "forecast_precipitation",
                5.0,
                unit="mm",
                location_id="outdoor",
            ),
        ],
    )

    patch = next(
        item
        for item in patches
        if item.target == "umbrella_advice"
    )

    assert patch.value == {
        "recommended": False,
        "reason": "low_rain_probability",
    }


def test_missing_rain_inputs_produces_no_umbrella_advice():
    capability = WeatherAdviceCapability()

    patches = capability.evaluate(
        interpretations=[],
        observations=[],
    )

    assert all(
        patch.target != "umbrella_advice"
        for patch in patches
    )

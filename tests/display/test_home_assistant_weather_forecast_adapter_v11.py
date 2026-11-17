from src.smartscreen_display.home_assistant_weather import (
    HomeAssistantWeatherForecastAdapter,
)


def make_adapter():
    return HomeAssistantWeatherForecastAdapter(
        entity_id="weather.demo_entity_065",
        location_id="outdoor",
    )


def by_parameter(observations):
    return {
        item.parameter: item
        for item in observations
    }


def test_current_weather_produces_temperature_observation():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 25.4,
                "temperature_unit": "°C",
                "humidity": 80,
            },
        }
    )

    items = by_parameter(observations)

    assert items["temperature"].value == 25.4
    assert items["temperature"].unit == "degC"
    assert items["temperature"].location_id == "outdoor"


def test_current_weather_produces_humidity_observation():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 25.4,
                "temperature_unit": "°C",
                "humidity": 80,
            },
        }
    )

    items = by_parameter(observations)

    assert items["humidity"].value == 80.0
    assert items["humidity"].unit == "percent"
    assert items["humidity"].location_id == "outdoor"


def test_hourly_forecast_produces_forecast_precipitation_observation():
    adapter = make_adapter()

    observations = adapter.convert_hourly_forecast(
        [
            {
                "condition": "partlycloudy",
                "datetime": "2026-08-13T12:00:00+00:00",
                "temperature": 25.2,
                "precipitation": 0.0,
                "humidity": 83,
            },
            {
                "condition": "rainy",
                "datetime": "2026-08-14T03:00:00+00:00",
                "temperature": 28.6,
                "precipitation": 0.2,
                "humidity": 66,
            },
        ]
    )

    items = by_parameter(observations)

    assert (
        items["forecast_precipitation"].value
        == 0.2
    )
    assert (
        items["forecast_precipitation"].unit
        == "mm"
    )
    assert (
        items["forecast_precipitation"].location_id
        == "outdoor"
    )


def test_hourly_forecast_preserves_weather_condition():
    adapter = make_adapter()

    observations = adapter.convert_hourly_forecast(
        [
            {
                "condition": "rainy",
                "datetime": "2026-08-14T03:00:00+00:00",
                "temperature": 28.6,
                "precipitation": 0.2,
                "humidity": 66,
            }
        ]
    )

    items = by_parameter(observations)

    assert (
        items["forecast_condition"].value
        == "rainy"
    )


def test_wrong_weather_entity_is_ignored():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.some_other_place",
            "state": "rainy",
            "attributes": {
                "temperature": 20,
                "humidity": 90,
            },
        }
    )

    assert observations == []


def test_hourly_forecast_only_uses_configured_horizon():
    adapter = HomeAssistantWeatherForecastAdapter(
        entity_id="weather.demo_entity_065",
        location_id="outdoor",
        forecast_horizon_hours=12,
    )

    observations = adapter.convert_hourly_forecast(
        [
            {
                "condition": "partlycloudy",
                "datetime": "2026-08-13T12:00:00+00:00",
                "precipitation": 0.0,
            },
            {
                "condition": "rainy",
                "datetime": "2026-08-13T18:00:00+00:00",
                "precipitation": 0.4,
            },
            {
                "condition": "rainy",
                "datetime": "2026-08-14T06:00:00+00:00",
                "precipitation": 5.0,
            },
        ],
        now="2026-08-13T12:00:00+00:00",
    )

    items = by_parameter(observations)

    assert (
        items["forecast_precipitation"].value
        == 0.4
    )


def test_hourly_forecast_excludes_past_entries():
    adapter = HomeAssistantWeatherForecastAdapter(
        entity_id="weather.demo_entity_065",
        location_id="outdoor",
        forecast_horizon_hours=12,
    )

    observations = adapter.convert_hourly_forecast(
        [
            {
                "condition": "rainy",
                "datetime": "2026-08-13T10:00:00+00:00",
                "precipitation": 9.0,
            },
            {
                "condition": "partlycloudy",
                "datetime": "2026-08-13T13:00:00+00:00",
                "precipitation": 0.1,
            },
        ],
        now="2026-08-13T12:00:00+00:00",
    )

    items = by_parameter(observations)

    assert (
        items["forecast_precipitation"].value
        == 0.1
    )


def test_hourly_forecast_condition_comes_from_horizon():
    adapter = HomeAssistantWeatherForecastAdapter(
        entity_id="weather.demo_entity_065",
        location_id="outdoor",
        forecast_horizon_hours=12,
    )

    observations = adapter.convert_hourly_forecast(
        [
            {
                "condition": "partlycloudy",
                "datetime": "2026-08-13T12:00:00+00:00",
                "precipitation": 0.0,
            },
            {
                "condition": "rainy",
                "datetime": "2026-08-14T20:00:00+00:00",
                "precipitation": 4.0,
            },
        ],
        now="2026-08-13T12:00:00+00:00",
    )

    items = by_parameter(observations)

    assert (
        items["forecast_condition"].value
        == "partlycloudy"
    )


def test_current_weather_produces_apparent_temperature():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 25.4,
                "temperature_unit": "°C",
                "humidity": 80,
                "wind_speed": 13.3,
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    apparent = items["apparent_temperature"]

    assert apparent.unit == "degC"
    assert apparent.location_id == "outdoor"

    # Expected apparent temperature is approximately
    # 27.4 °C for the supplied weather conditions.
    assert round(apparent.value, 1) == 27.4


def test_current_weather_apparent_temperature_has_weather_provenance():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "cloudy",
            "attributes": {
                "temperature": 20,
                "humidity": 70,
                "wind_speed": 10,
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    apparent = items["apparent_temperature"]

    assert apparent.provenance[
        "provider"
    ] == "home_assistant"

    assert apparent.provenance[
        "entity_id"
    ] == "weather.demo_entity_065"

    assert apparent.provenance[
        "source"
    ] == "weather_current"


def test_current_weather_without_wind_does_not_invent_apparent_temperature():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 25.4,
                "humidity": 80,
            },
        }
    )

    items = by_parameter(observations)

    assert "apparent_temperature" not in items


def test_current_weather_invalid_wind_does_not_produce_apparent_temperature():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 25.4,
                "humidity": 80,
                "wind_speed": "unknown",
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    assert "apparent_temperature" not in items


def test_current_weather_converts_kmh_wind_for_apparent_temperature():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 10,
                "humidity": 50,
                "wind_speed": 36,
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    apparent = items["apparent_temperature"]

    # 36 km/h == 10 m/s.
    assert apparent.value < 10


def test_current_weather_produces_weather_condition_observation():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 25.4,
                "temperature_unit": "°C",
                "humidity": 80,
                "wind_speed": 13.3,
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    condition = items[
        "weather_condition"
    ]

    assert condition.value == "partlycloudy"
    assert condition.location_id == "outdoor"
    assert (
        condition.provenance["provider"]
        == "home_assistant"
    )
    assert (
        condition.provenance["source"]
        == "weather_current"
    )


def test_current_weather_produces_wind_speed_observation():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "cloudy",
            "attributes": {
                "temperature": 20,
                "humidity": 70,
                "wind_speed": 13.3,
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    wind = items["wind_speed"]

    assert wind.value == 13.3
    assert wind.unit == "km/h"
    assert wind.location_id == "outdoor"
    assert (
        wind.provenance["provider"]
        == "home_assistant"
    )
    assert (
        wind.provenance["source"]
        == "weather_current"
    )


def test_current_weather_invalid_wind_is_not_exposed():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "cloudy",
            "attributes": {
                "temperature": 20,
                "humidity": 70,
                "wind_speed": "unknown",
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    assert "wind_speed" not in items


def test_current_weather_empty_condition_is_not_exposed():
    adapter = make_adapter()

    observations = adapter.convert_current(
        {
            "entity_id": "weather.demo_entity_065",
            "state": "",
            "attributes": {
                "temperature": 20,
                "humidity": 70,
                "wind_speed": 10,
                "wind_speed_unit": "km/h",
            },
        }
    )

    items = by_parameter(observations)

    assert (
        "weather_condition"
        not in items
    )

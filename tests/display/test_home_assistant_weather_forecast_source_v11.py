from src.smartscreen_display.home_assistant_weather import (
    HomeAssistantWeatherForecastAdapter,
    HomeAssistantWeatherForecastSource,
)
from src.smartscreen_platform.capabilities.weather_advice import (
    WeatherAdviceCapability,
)
from src.smartscreen_platform.capabilities.weather_status import (
    WeatherStatusCapability,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)


class FakeClient:
    def get_json(self, path):
        return {
            "entity_id": "weather.demo_entity_065",
            "state": "unknown",
            "attributes": {},
        }

    def post_json(
        self,
        path,
        payload,
    ):
        assert (
            path
            == "/api/services/weather/"
            "get_forecasts?return_response"
        )

        assert payload == {
            "entity_id": "weather.demo_entity_065",
            "type": "hourly",
        }

        return {
            "changed_states": [],
            "service_response": {
                "weather.demo_entity_065": {
                    "forecast": [
                        {
                            "condition": "partlycloudy",
                            "datetime": (
                                "2026-08-13T12:00:00+00:00"
                            ),
                            "precipitation": 0.0,
                        },
                        {
                            "condition": "rainy",
                            "datetime": (
                                "2026-08-13T18:00:00+00:00"
                            ),
                            "precipitation": 0.4,
                        },
                    ]
                }
            },
        }


def make_source():
    household_state = HouseholdStateEngine()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            (
                "outdoor",
                "forecast_precipitation",
            ): 3600,
            (
                "outdoor",
                "forecast_condition",
            ): 3600,
        },
    )

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[],
        capabilities=[
            WeatherAdviceCapability(),
            WeatherStatusCapability(),
        ],
    )

    adapter = HomeAssistantWeatherForecastAdapter(
        entity_id="weather.demo_entity_065",
        location_id="outdoor",
        forecast_horizon_hours=12,
    )

    source = HomeAssistantWeatherForecastSource(
        base_url="http://ha.local",
        token="secret",
        entity_id="weather.demo_entity_065",
        adapter=adapter,
        observation_accumulator=accumulator,
        observation_sink=pipeline,
        client=FakeClient(),
        clock=lambda: (
            "2026-08-13T12:00:00+00:00"
        ),
    )

    return source, household_state


def test_forecast_source_projects_service_response_into_weather_advice():
    source, household_state = make_source()

    observations = source.run_once()

    assert any(
        item.parameter == "forecast_precipitation"
        and item.value == 0.4
        and item.location_id == "outdoor"
        for item in observations
    )

    umbrella = household_state.get(
        "umbrella_advice",
        location_id="outdoor",
    )

    assert umbrella is not None
    assert umbrella.value["recommended"] is True
    assert (
        umbrella.value["reason"]
        == "forecast_precipitation"
    )


def test_forecast_source_preserves_forecast_condition():
    source, household_state = make_source()

    observations = source.run_once()

    condition = next(
        item
        for item in observations
        if item.parameter == "forecast_condition"
    )

    assert condition.location_id == "outdoor"
    assert condition.value == "partlycloudy"


def test_forecast_source_ignores_invalid_service_response():
    source, household_state = make_source()

    source._client = type(
        "InvalidClient",
        (),
        {
            "get_json": lambda self, path: {
                "entity_id": (
                    "weather.demo_entity_065"
                ),
                "state": "unknown",
                "attributes": {},
            },
            "post_json": lambda self, path, payload: {
                "service_response": {}
            },
        },
    )()

    observations = source.run_once()

    assert observations == []
    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is None
    )


def test_forecast_source_reads_current_weather_state():
    source, household_state = make_source()

    calls = []

    class CurrentWeatherClient:
        def get_json(self, path):
            calls.append(("get", path))

            return {
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

        def post_json(self, path, payload):
            calls.append(("post", path))

            return {
                "service_response": {
                    "weather.demo_entity_065": {
                        "forecast": []
                    }
                }
            }

    source._client = CurrentWeatherClient()

    observations = source.run_once()

    assert (
        "get",
        "/api/states/weather.demo_entity_065",
    ) in calls

    assert any(
        item.parameter == "apparent_temperature"
        and item.location_id == "outdoor"
        for item in observations
    )

    clothing = household_state.get(
        "clothing_advice",
        location_id="outdoor",
    )

    assert clothing is not None


def test_forecast_source_combines_current_and_forecast_observations():
    source, household_state = make_source()

    class CombinedWeatherClient:
        def get_json(self, path):
            return {
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

        def post_json(self, path, payload):
            return {
                "service_response": {
                    "weather.demo_entity_065": {
                        "forecast": [
                            {
                                "condition": "rainy",
                                "datetime": (
                                    "2026-08-13T18:00:00+00:00"
                                ),
                                "precipitation": 0.4,
                            }
                        ]
                    }
                }
            }

    source._client = CombinedWeatherClient()
    source._clock = lambda: (
        "2026-08-13T12:00:00+00:00"
    )

    observations = source.run_once()

    parameters = {
        item.parameter
        for item in observations
    }

    assert "apparent_temperature" in parameters
    assert "forecast_precipitation" in parameters

    assert (
        household_state.get(
            "clothing_advice",
            location_id="outdoor",
        )
        is not None
    )

    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is not None
    )


def test_forecast_source_uses_short_retry_interval_after_failure():
    source, _ = make_source()

    waits = []

    class FakeStopEvent:
        def is_set(self):
            return False

        def wait(self, timeout):
            waits.append(timeout)
            return True

    def fail_once():
        raise RuntimeError("temporary weather failure")

    source._stop_event = FakeStopEvent()
    source.run_once = fail_once

    source._run_background()

    assert waits == [30.0]


def test_forecast_source_keeps_current_weather_when_forecast_request_fails():
    source, household_state = make_source()

    class CurrentOnlyClient:
        def get_json(self, path):
            return {
                "entity_id": (
                    "weather.demo_entity_065"
                ),
                "state": "cloudy",
                "attributes": {
                    "temperature": 27.8,
                    "temperature_unit": "°C",
                    "humidity": 72,
                    "wind_speed": 13.0,
                    "wind_speed_unit": "km/h",
                },
            }

        def post_json(self, path, payload):
            raise RuntimeError(
                "forecast temporarily unavailable"
            )

    source._client = CurrentOnlyClient()

    observations = source.run_once()

    parameters = {
        item.parameter
        for item in observations
    }

    assert "weather_condition" in parameters
    assert "temperature" in parameters
    assert "humidity" in parameters
    assert "wind_speed" in parameters
    assert "apparent_temperature" in parameters

    weather_status = household_state.get(
        "weather_status",
        location_id="outdoor",
    )

    assert weather_status is not None
    assert (
        weather_status.value["condition"]
        == "cloudy"
    )
    assert (
        weather_status.value["temperature"]
        == 27.8
    )

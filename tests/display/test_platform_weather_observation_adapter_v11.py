from pathlib import Path

from src.smartscreen_display.home_assistant_observations import (
    HomeAssistantObservationAdapter,
)
from src.smartscreen_display.platform_entities_config import (
    load_platform_entities,
)


PROJECT = Path(__file__).resolve().parents[2]

PLATFORM_ENTITIES = (
    PROJECT
    / "config"
    / "platform_entities.json"
)


def default_adapter():
    return HomeAssistantObservationAdapter(
        entities=load_platform_entities(
            PLATFORM_ENTITIES
        )
    )








def test_unknown_weather_sensor_is_not_implicitly_accepted():
    adapter = default_adapter()

    observations = adapter.convert(
        {
            "entity_id": "sensor.random_weather_value",
            "state": "42",
            "attributes": {},
        }
    )

    assert observations == []


def test_unavailable_default_weather_sensor_produces_no_observation():
    adapter = default_adapter()

    observations = adapter.convert(
        {
            "entity_id": (
                "sensor."
                "outdoor_apparent_temperature"
            ),
            "state": "unavailable",
            "attributes": {},
        }
    )

    assert observations == []

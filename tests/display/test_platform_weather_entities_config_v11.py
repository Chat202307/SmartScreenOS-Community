from pathlib import Path

from src.smartscreen_display.platform_entities_config import (
    load_platform_entities,
)


PROJECT = Path(__file__).resolve().parents[2]

PLATFORM_ENTITIES = (
    PROJECT
    / "config"
    / "platform_entities.json"
)


def weather_entities():
    entities = load_platform_entities(
        PLATFORM_ENTITIES
    )

    return {
        item["parameter"]: item
        for item in entities
        if item["parameter"] in {
            "precipitation_probability",
            "apparent_temperature",
        }
    }













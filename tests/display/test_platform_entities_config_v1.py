import json

from src.smartscreen_display.platform_entities_config import (
    load_platform_entities,
)


def test_load_platform_entities(tmp_path):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "sensor.living_temperature",
                        "parameter": "temperature",
                        "location_id": "living",
                        "value_type": "float",
                    },
                    {
                        "entity_id": "sensor.living_humidity",
                        "parameter": "humidity",
                        "location_id": "living",
                        "value_type": "float",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "sensor.living_temperature",
            "parameter": "temperature",
            "location_id": "living",
            "value_type": "float",
        },
        {
            "entity_id": "sensor.living_humidity",
            "parameter": "humidity",
            "location_id": "living",
            "value_type": "float",
        },
    ]


def test_load_platform_entities_missing_file(tmp_path):
    assert (
        load_platform_entities(
            tmp_path / "missing.json"
        )
        == []
    )


def test_load_platform_entities_invalid_json(tmp_path):
    path = tmp_path / "platform_entities.json"
    path.write_text(
        "{ invalid",
        encoding="utf-8",
    )

    assert load_platform_entities(path) == []


def test_load_platform_entities_ignores_invalid_entries(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "sensor.valid",
                        "parameter": "temperature",
                        "location_id": "living",
                        "value_type": "float",
                    },
                    {
                        "entity_id": "",
                        "parameter": "humidity",
                    },
                    {
                        "entity_id": "sensor.no_parameter",
                    },
                    "invalid",
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "sensor.valid",
            "parameter": "temperature",
            "location_id": "living",
            "value_type": "float",
        }
    ]


def test_load_platform_entities_rejects_invalid_value_type(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "sensor.valid",
                        "parameter": "temperature",
                        "value_type": "float",
                    },
                    {
                        "entity_id": "sensor.invalid",
                        "parameter": "temperature",
                        "value_type": "decimal",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "sensor.valid",
            "parameter": "temperature",
            "value_type": "float",
        }
    ]


def test_load_platform_entities_preserves_max_age_seconds(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "binary_sensor.living_presence",
                        "parameter": "presence",
                        "location_id": "living",
                        "value_type": "bool",
                        "max_age_seconds": 60,
                    },
                    {
                        "entity_id": "sensor.living_temperature",
                        "parameter": "temperature",
                        "location_id": "living",
                        "value_type": "float",
                        "max_age_seconds": 300,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "binary_sensor.living_presence",
            "parameter": "presence",
            "location_id": "living",
            "value_type": "bool",
            "max_age_seconds": 60,
        },
        {
            "entity_id": "sensor.living_temperature",
            "parameter": "temperature",
            "location_id": "living",
            "value_type": "float",
            "max_age_seconds": 300,
        },
    ]


def test_load_platform_entities_rejects_invalid_max_age_seconds(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "sensor.valid",
                        "parameter": "temperature",
                        "value_type": "float",
                        "max_age_seconds": 300,
                    },
                    {
                        "entity_id": "sensor.zero",
                        "parameter": "temperature",
                        "value_type": "float",
                        "max_age_seconds": 0,
                    },
                    {
                        "entity_id": "sensor.negative",
                        "parameter": "temperature",
                        "value_type": "float",
                        "max_age_seconds": -1,
                    },
                    {
                        "entity_id": "sensor.string",
                        "parameter": "temperature",
                        "value_type": "float",
                        "max_age_seconds": "60",
                    },
                    {
                        "entity_id": "sensor.boolean",
                        "parameter": "temperature",
                        "value_type": "float",
                        "max_age_seconds": True,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "sensor.valid",
            "parameter": "temperature",
            "value_type": "float",
            "max_age_seconds": 300,
        }
    ]


def test_load_platform_entities_allows_missing_max_age_seconds(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "sensor.temperature",
                        "parameter": "temperature",
                        "value_type": "float",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "sensor.temperature",
            "parameter": "temperature",
            "value_type": "float",
        }
    ]


def test_load_platform_entities_preserves_location_specific_max_age(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "binary_sensor.living_presence",
                        "parameter": "presence",
                        "location_id": "living",
                        "value_type": "bool",
                        "max_age_seconds": 60,
                    },
                    {
                        "entity_id": "binary_sensor.bedroom_presence",
                        "parameter": "presence",
                        "location_id": "bedroom",
                        "value_type": "bool",
                        "max_age_seconds": 120,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_platform_entities(path) == [
        {
            "entity_id": "binary_sensor.living_presence",
            "parameter": "presence",
            "location_id": "living",
            "value_type": "bool",
            "max_age_seconds": 60,
        },
        {
            "entity_id": "binary_sensor.bedroom_presence",
            "parameter": "presence",
            "location_id": "bedroom",
            "value_type": "bool",
            "max_age_seconds": 120,
        },
    ]


def test_load_platform_entities_preserves_same_parameter_different_ttl(
    tmp_path,
):
    path = tmp_path / "platform_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "sensor.living_temperature",
                        "parameter": "temperature",
                        "location_id": "living",
                        "value_type": "float",
                        "max_age_seconds": 300,
                    },
                    {
                        "entity_id": "sensor.bedroom_temperature",
                        "parameter": "temperature",
                        "location_id": "bedroom",
                        "value_type": "float",
                        "max_age_seconds": 600,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    entities = load_platform_entities(path)

    assert entities[0]["max_age_seconds"] == 300
    assert entities[1]["max_age_seconds"] == 600

    assert entities[0]["location_id"] == "living"
    assert entities[1]["location_id"] == "bedroom"

import json

from src.smartscreen_display.device_data_config import (
    load_device_definitions,
)


def test_config_loads_parameter_observation_location(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "devices": [
                    {
                        "device_id": "kitchen.sensor_1",
                        "name": "厨房人体",
                        "location_id": "kitchen",
                        "adapter_id": "home_assistant",
                        "parameters": {
                            "presence": {
                                "source_id": (
                                    "binary_sensor."
                                    "kitchen_presence"
                                ),
                                "value_type": "bool",
                                "observation_location_id": (
                                    "open_public_area"
                                ),
                            },
                            "illuminance": {
                                "source_id": (
                                    "sensor.kitchen_lux"
                                ),
                                "value_type": "float",
                                "unit": "lux",
                            },
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1

    presence = (
        devices[0]
        .parameters["presence"]
    )

    illuminance = (
        devices[0]
        .parameters["illuminance"]
    )

    assert (
        presence.observation_location_id
        == "open_public_area"
    )

    assert (
        illuminance.observation_location_id
        is None
    )


def test_config_rejects_empty_parameter_observation_location(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "devices": [
                    {
                        "device_id": "kitchen.sensor_1",
                        "name": "厨房人体",
                        "location_id": "kitchen",
                        "adapter_id": "home_assistant",
                        "parameters": {
                            "presence": {
                                "source_id": (
                                    "binary_sensor."
                                    "kitchen_presence"
                                ),
                                "value_type": "bool",
                                "observation_location_id": "",
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert load_device_definitions(path) == []


def test_config_rejects_non_string_parameter_observation_location(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "devices": [
                    {
                        "device_id": "kitchen.sensor_1",
                        "name": "厨房人体",
                        "location_id": "kitchen",
                        "adapter_id": "home_assistant",
                        "parameters": {
                            "presence": {
                                "source_id": (
                                    "binary_sensor."
                                    "kitchen_presence"
                                ),
                                "value_type": "bool",
                                "observation_location_id": 123,
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert load_device_definitions(path) == []

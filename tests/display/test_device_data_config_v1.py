from pathlib import Path

from src.smartscreen_display.device_data_config import (
    load_device_definitions,
)


def test_loader_reads_devices_and_parameters(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.presence_sensor_1",
      "name": "客厅人体",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "presence": {
          "source_id": "binary_sensor.living_presence",
          "value_type": "bool"
        },
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1

    device = devices[0]

    assert device.device_id == (
        "living.presence_sensor_1"
    )
    assert device.name == "客厅人体"
    assert device.location_id == "living"
    assert device.adapter_id == (
        "home_assistant"
    )

    assert set(device.parameters) == {
        "presence",
        "illuminance",
    }

    assert (
        device.parameters[
            "illuminance"
        ].source_id
        == "sensor.living_illuminance"
    )

    assert (
        device.parameters[
            "illuminance"
        ].unit
        == "lux"
    )


def test_loader_returns_empty_for_missing_file(
    tmp_path,
):
    path = (
        tmp_path
        / "missing.json"
    )

    assert (
        load_device_definitions(
            path
        )
        == []
    )


def test_loader_skips_invalid_device(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "",
      "name": "Invalid",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    assert (
        load_device_definitions(
            path
        )
        == []
    )


def test_device_data_config_preserves_parameter_max_age_seconds(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "presence": {
          "source_id": "binary_sensor.living_presence",
          "value_type": "bool",
          "max_age_seconds": 60
        },
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux",
          "max_age_seconds": 300
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1

    presence = devices[0].parameters[
        "presence"
    ]

    illuminance = devices[0].parameters[
        "illuminance"
    ]

    assert presence.max_age_seconds == 60
    assert illuminance.max_age_seconds == 300


def test_device_data_config_allows_missing_parameter_max_age_seconds(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1

    assert (
        devices[0]
        .parameters["illuminance"]
        .max_age_seconds
        is None
    )


def test_device_data_config_rejects_invalid_parameter_max_age_seconds(
    tmp_path,
):
    invalid_values = [
        0,
        -1,
        True,
        "60",
    ]

    for invalid_value in invalid_values:
        path = tmp_path / (
            "device_data_"
            + str(invalid_value)
            .replace("-", "negative_")
            + ".json"
        )

        import json

        payload = {
            "schema_version": 1,
            "devices": [
                {
                    "device_id": (
                        "living.sensor_1"
                    ),
                    "name": "客厅传感器",
                    "location_id": "living",
                    "adapter_id": (
                        "home_assistant"
                    ),
                    "parameters": {
                        "presence": {
                            "source_id": (
                                "binary_sensor."
                                "living_presence"
                            ),
                            "value_type": "bool",
                            "max_age_seconds": (
                                invalid_value
                            ),
                        }
                    },
                }
            ],
        }

        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        assert (
            load_device_definitions(
                path
            )
            == []
        )




def test_device_data_config_allows_missing_controls(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1
    assert devices[0].controls == {}


def test_device_data_config_loads_controls(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.purifier_1",
      "name": "空气净化器",
      "location_id": "living",
      "adapter_id": "xingoo",
      "parameters": {
        "power": {
          "source_id": "iot:PowerSwitch",
          "value_type": "bool"
        },
        "mode": {
          "source_id": "iot:WorkMode",
          "value_type": "int"
        }
      },
      "controls": {
        "power": {
          "parameter": "power",
          "kind": "boolean"
        },
        "mode": {
          "parameter": "mode",
          "kind": "select",
          "options": [
            "smart",
            "sleep"
          ]
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1

    controls = devices[0].controls

    assert set(controls) == {
        "power",
        "mode",
    }

    assert (
        controls["power"].control_id
        == "power"
    )
    assert (
        controls["power"].parameter
        == "power"
    )
    assert (
        controls["power"].kind
        == "boolean"
    )
    assert (
        controls["power"].options
        == ()
    )

    assert (
        controls["mode"].parameter
        == "mode"
    )
    assert (
        controls["mode"].kind
        == "select"
    )
    assert (
        controls["mode"].options
        == (
            "smart",
            "sleep",
        )
    )


def test_device_data_config_rejects_non_object_controls(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.purifier_1",
      "name": "空气净化器",
      "location_id": "living",
      "adapter_id": "xingoo",
      "parameters": {},
      "controls": []
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    assert (
        load_device_definitions(
            path
        )
        == []
    )


def test_device_data_config_rejects_invalid_control_definition(
    tmp_path,
):
    invalid_controls = [
        {
            "power": {
                "kind": "boolean",
            }
        },
        {
            "power": {
                "parameter": "power",
            }
        },
        {
            "power": {
                "parameter": "power",
                "kind": "boolean",
                "options": "invalid",
            }
        },
    ]

    import json

    for index, controls in enumerate(
        invalid_controls
    ):
        path = tmp_path / (
            "device_data_control_"
            + str(index)
            + ".json"
        )

        payload = {
            "schema_version": 1,
            "devices": [
                {
                    "device_id": (
                        "living.purifier_1"
                    ),
                    "name": "空气净化器",
                    "location_id": "living",
                    "adapter_id": "xingoo",
                    "parameters": {
                        "power": {
                            "source_id": (
                                "iot:PowerSwitch"
                            ),
                            "value_type": (
                                "bool"
                            ),
                        }
                    },
                    "controls": controls,
                }
            ],
        }

        path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        assert (
            load_device_definitions(
                path
            )
            == []
        )


def test_device_data_config_loads_adapter_config(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "corridor.light_1",
      "name": "走廊灯",
      "location_id": "corridor",
      "adapter_id": "home_assistant",
      "adapter_config": {
        "entity_id": "light.corridor"
      },
      "parameters": {
        "power": {
          "source_id": "light.corridor",
          "value_type": "bool"
        }
      },
      "controls": {
        "power": {
          "parameter": "power",
          "kind": "boolean"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1

    assert devices[0].adapter_config == {
        "entity_id": "light.corridor",
    }


def test_device_data_config_allows_missing_adapter_config(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1
    assert devices[0].adapter_config == {}


def test_device_data_config_rejects_non_object_adapter_config(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "corridor.light_1",
      "name": "走廊灯",
      "location_id": "corridor",
      "adapter_id": "home_assistant",
      "adapter_config": [],
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    assert (
        load_device_definitions(
            path
        )
        == []
    )


def test_device_data_config_loads_optional_device_type(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "air_purifier_001",
      "device_type": "air_purifier",
      "name": "空气净化器",
      "location_id": "living",
      "adapter_id": "xingoo",
      "parameters": {
        "power": {
          "source_id": "device:PowerSwitch",
          "value_type": "bool"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(
        path
    )

    assert len(devices) == 1
    assert (
        devices[0].device_id
        == "air_purifier_001"
    )
    assert (
        devices[0].device_type
        == "air_purifier"
    )


def test_device_data_config_rejects_invalid_device_type(
    tmp_path,
):
    for index, invalid_value in enumerate(
        (
            "",
            "   ",
            123,
            True,
        )
    ):
        import json

        path = tmp_path / (
            "device_data_type_"
            + str(index)
            + ".json"
        )

        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "devices": [
                        {
                            "device_id": (
                                "air_purifier_001"
                            ),
                            "device_type": (
                                invalid_value
                            ),
                            "name": (
                                "空气净化器"
                            ),
                            "location_id": (
                                "living"
                            ),
                            "adapter_id": (
                                "xingoo"
                            ),
                            "parameters": {},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        assert (
            load_device_definitions(
                path
            )
            == []
        )

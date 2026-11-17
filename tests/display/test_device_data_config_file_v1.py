from pathlib import Path

import pytest

from src.smartscreen_display.device_data_config import (
    load_device_definitions,
)
from src.smartscreen_platform.device_data import (
    DeviceRegistry,
)


PROJECT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CONFIG = (
    PROJECT
    / "config"
    / "device_data.json"
)


def load_registry():
    devices = load_device_definitions(
        CONFIG
    )

    return (
        devices,
        DeviceRegistry(
            devices=devices
        ),
    )



















def test_read_only_devices_have_no_controls():
    devices, _ = load_registry()

    controlled_device_ids = {
        "corridor.light_1",
        "corridor.water_heater_1",
        "living.main_light_power_1",
        "living.main_light_1",
        "living.light_strip_1",
        "living.downlight_1",
        "master_bedroom.light_strip_1",
        "master_bedroom.downlight_1",
        "master_bedroom.main_light_power_1",
        "master_bedroom.main_light_1",
        "master_bedroom.air_conditioner_1",
        "study.ceiling_light_1",
        "study.air_conditioner_1",
        "dining.atmosphere_light_1",
        "air_conditioner_001",
        "living.curtain_1",
        "master_bedroom.curtain_1",
        "dining.light_power_1",
        "dining.table_light_east",
        "dining.table_light_center",
        "dining.table_light_west",
        "kitchen.light_1",
        "kitchen.dishwasher_1",
        "princess_room.spotlight_1",
        "princess_room.light_strip_1",
        "princess_room.ceiling_light_power_1",
        "princess_room.ceiling_light_1",
        "princess_room.air_conditioner_1",
        "princess_room.curtain_1",
        "master_bath.makeup_light_1",
        "master_bath.bathing_light_1",
        "guest_bath.makeup_light_1",
        "guest_bath.bathing_light_1",
        "air_purifier_001",
        "vacuum_001",
    }

    for device in devices:
        if (
            device.device_id
            in controlled_device_ids
        ):
            continue

        assert device.controls == {}












def test_loader_reads_power_control_device_id(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "room.smart_light_1",
      "name": "智能灯",
      "location_id": "room",
      "adapter_id": "home_assistant",
      "power_control_device_id": "room.light_power_1",
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

    assert (
        devices[0].power_control_device_id
        == "room.light_power_1"
    )


def test_loader_rejects_blank_power_control_device_id(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "room.smart_light_1",
      "name": "智能灯",
      "location_id": "room",
      "adapter_id": "home_assistant",
      "power_control_device_id": "   ",
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    assert load_device_definitions(
        path
    ) == []


def test_loader_reads_power_source_device_id(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "dining.table_light_east",
      "name": "餐桌灯东",
      "location_id": "dining",
      "adapter_id": "home_assistant",
      "power_source_device_id": "dining.light_power_1",
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

    assert (
        devices[0].power_source_device_id
        == "dining.light_power_1"
    )


def test_loader_rejects_blank_power_source_device_id(
    tmp_path,
):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "dining.table_light_east",
      "name": "餐桌灯东",
      "location_id": "dining",
      "adapter_id": "home_assistant",
      "power_source_device_id": "   ",
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    assert load_device_definitions(
        path
    ) == []





















































def test_loader_reads_area_readonly(tmp_path):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "room.door_1",
      "name": "门磁",
      "location_id": "room",
      "adapter_id": "home_assistant",
      "area_readonly": true,
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    devices = load_device_definitions(path)

    assert len(devices) == 1
    assert devices[0].area_readonly is True


def test_loader_rejects_non_boolean_area_readonly(tmp_path):
    path = tmp_path / "device_data.json"

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "room.door_1",
      "name": "门磁",
      "location_id": "room",
      "adapter_id": "home_assistant",
      "area_readonly": "yes",
      "parameters": {}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    assert load_device_definitions(path) == []





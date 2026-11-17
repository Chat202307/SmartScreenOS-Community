import pytest

from src.smartscreen_platform.device_data import (
    DeviceDefinition,
)



def test_device_definition_can_reference_power_source_device():
    device = DeviceDefinition(
        device_id="dining.table_light_east",
        name="餐桌灯东",
        location_id="dining",
        adapter_id="home_assistant",
        parameters={},
        power_source_device_id=(
            "dining.light_power_1"
        ),
    )

    assert (
        device.power_source_device_id
        == "dining.light_power_1"
    )


def test_device_definition_defaults_to_no_power_source():
    device = DeviceDefinition(
        device_id="living.light_1",
        name="客厅灯",
        location_id="living",
        adapter_id="home_assistant",
        parameters={},
    )

    assert (
        device.power_source_device_id
        is None
    )


def test_device_definition_rejects_blank_power_source_device_id():
    with pytest.raises(ValueError):
        DeviceDefinition(
            device_id="dining.table_light_east",
            name="餐桌灯东",
            location_id="dining",
            adapter_id="home_assistant",
            parameters={},
            power_source_device_id="   ",
        )

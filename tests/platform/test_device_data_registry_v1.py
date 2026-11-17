import pytest

from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceRegistry,
    DeviceRegistryError,
)


def make_living_sensor():
    return DeviceDefinition(
        device_id="living.presence_sensor_1",
        name="客厅人体",
        location_id="living",
        adapter_id="home_assistant",
        parameters={
            "presence": DeviceParameterDefinition(
                parameter="presence",
                source_id=(
                    "binary_sensor."
                    "xiaomi_presence"
                ),
                value_type="bool",
            ),
            "illuminance": DeviceParameterDefinition(
                parameter="illuminance",
                source_id=(
                    "sensor."
                    "xiaomi_illuminance"
                ),
                value_type="float",
                unit="lux",
            ),
        },
    )


def test_registry_preserves_device_parameters():
    device = make_living_sensor()

    registry = DeviceRegistry(
        devices=[device]
    )

    resolved = registry.get(
        "living.presence_sensor_1"
    )

    assert resolved is device

    assert set(resolved.parameters) == {
        "presence",
        "illuminance",
    }

    assert (
        resolved.parameters[
            "illuminance"
        ].unit
        == "lux"
    )


def test_registry_resolves_source_to_device_parameter():
    registry = DeviceRegistry(
        devices=[
            make_living_sensor()
        ]
    )

    binding = registry.resolve_source(
        adapter_id="home_assistant",
        source_id="sensor.xiaomi_illuminance",
    )

    assert binding.device_id == (
        "living.presence_sensor_1"
    )
    assert binding.location_id == "living"
    assert binding.parameter == "illuminance"
    assert binding.value_type == "float"
    assert binding.unit == "lux"


def test_duplicate_device_id_is_rejected():
    device = make_living_sensor()

    with pytest.raises(
        DeviceRegistryError
    ):
        DeviceRegistry(
            devices=[
                device,
                device,
            ]
        )


def test_duplicate_adapter_source_is_rejected():
    first = make_living_sensor()

    second = DeviceDefinition(
        device_id="corridor.sensor_1",
        name="走廊传感器",
        location_id="corridor",
        adapter_id="home_assistant",
        parameters={
            "illuminance": (
                DeviceParameterDefinition(
                    parameter="illuminance",
                    source_id=(
                        "sensor."
                        "xiaomi_illuminance"
                    ),
                    value_type="float",
                    unit="lux",
                )
            )
        },
    )

    with pytest.raises(
        DeviceRegistryError
    ):
        DeviceRegistry(
            devices=[
                first,
                second,
            ]
        )


def test_parameter_key_must_match_definition_parameter():
    with pytest.raises(
        ValueError
    ):
        DeviceDefinition(
            device_id="living.sensor_1",
            name="客厅传感器",
            location_id="living",
            adapter_id="home_assistant",
            parameters={
                "presence": (
                    DeviceParameterDefinition(
                        parameter="illuminance",
                        source_id="sensor.x",
                        value_type="float",
                        unit="lux",
                    )
                )
            },
        )


def test_registry_returns_none_for_unknown_source():
    registry = DeviceRegistry(
        devices=[
            make_living_sensor()
        ]
    )

    assert (
        registry.resolve_source(
            adapter_id="home_assistant",
            source_id="sensor.unknown",
        )
        is None
    )


def test_registry_all_preserves_registered_devices():
    first = make_living_sensor()

    second = DeviceDefinition(
        device_id="corridor.motion_sensor_1",
        name="过廊人体",
        location_id="corridor",
        adapter_id="home_assistant",
        parameters={
            "motion_idle_seconds": (
                DeviceParameterDefinition(
                    parameter=(
                        "motion_idle_seconds"
                    ),
                    source_id=(
                        "sensor.corridor_motion"
                    ),
                    value_type="int",
                    unit="s",
                )
            )
        },
    )

    registry = DeviceRegistry(
        devices=[
            first,
            second,
        ]
    )

    assert registry.all() == [
        first,
        second,
    ]

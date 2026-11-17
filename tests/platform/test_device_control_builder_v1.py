import pytest

from src.smartscreen_platform.device_control.builder import (
    build_device_control_bindings,
)
from src.smartscreen_platform.device_control.model import (
    DeviceControlDefinition,
)
from src.smartscreen_platform.device_data.model import (
    DeviceDefinition,
)


def create_device(
    *,
    controls=None,
):
    return DeviceDefinition(
        device_id=(
            "xingoo_test_device_1"
        ),
        name="IAM消毒空气净化器",
        location_id="open_public_area",
        adapter_id="xingoo",
        parameters={},
        controls=(
            controls
            if controls is not None
            else {}
        ),
    )


def test_device_definition_accepts_controls():
    power = DeviceControlDefinition(
        control_id="power",
        kind="boolean",
        parameter="power",
    )

    device = create_device(
        controls={
            "power": power,
        }
    )

    assert device.controls == {
        "power": power,
    }


def test_device_definition_copies_controls():
    controls = {
        "power": DeviceControlDefinition(
            control_id="power",
            kind="boolean",
            parameter="power",
        ),
    }

    device = create_device(
        controls=controls
    )

    controls.clear()

    assert "power" in device.controls


def test_device_definition_rejects_invalid_control():
    with pytest.raises(
        TypeError,
        match="DeviceControlDefinition",
    ):
        create_device(
            controls={
                "power": object(),
            }
        )


def test_device_definition_requires_matching_control_key():
    with pytest.raises(
        ValueError,
        match="control key",
    ):
        create_device(
            controls={
                "wrong": (
                    DeviceControlDefinition(
                        control_id="power",
                        kind="boolean",
                        parameter="power",
                    )
                ),
            }
        )


def test_builder_creates_binding_for_each_control():
    device = create_device(
        controls={
            "power": DeviceControlDefinition(
                control_id="power",
                kind="boolean",
                parameter="power",
            ),
            "mode": DeviceControlDefinition(
                control_id="mode",
                kind="select",
                parameter="mode",
                options=(
                    "smart",
                    "sleep",
                ),
            ),
        }
    )

    bindings = (
        build_device_control_bindings(
            devices=[
                device,
            ]
        )
    )

    assert len(bindings) == 2

    by_control = {
        binding.control.control_id:
            binding
        for binding in bindings
    }

    assert set(by_control) == {
        "power",
        "mode",
    }

    assert (
        by_control["power"].device_id
        == device.device_id
    )

    assert (
        by_control["power"].adapter_id
        == "xingoo"
    )

    assert (
        by_control["power"].control
        is device.controls["power"]
    )


def test_builder_supports_multiple_devices():
    first = create_device(
        controls={
            "power": DeviceControlDefinition(
                control_id="power",
                kind="boolean",
                parameter="power",
            ),
        }
    )

    second = DeviceDefinition(
        device_id="bedroom.device_1",
        name="Bedroom device",
        location_id="bedroom",
        adapter_id="other",
        parameters={},
        controls={
            "enabled": (
                DeviceControlDefinition(
                    control_id="enabled",
                    kind="boolean",
                    parameter="enabled",
                )
            ),
        },
    )

    bindings = (
        build_device_control_bindings(
            devices=[
                first,
                second,
            ]
        )
    )

    assert {
        (
            binding.device_id,
            binding.adapter_id,
            binding.control.control_id,
        )
        for binding in bindings
    } == {
        (
            first.device_id,
            "xingoo",
            "power",
        ),
        (
            second.device_id,
            "other",
            "enabled",
        ),
    }


def test_builder_ignores_devices_without_controls():
    device = create_device()

    assert (
        build_device_control_bindings(
            devices=[
                device,
            ]
        )
        == []
    )


def test_device_definition_preserves_adapter_config():
    from src.smartscreen_platform.device_data import (
        DeviceDefinition,
    )

    device = DeviceDefinition(
        device_id="corridor.light_1",
        name="走廊灯",
        location_id="corridor",
        adapter_id="home_assistant",
        parameters={},
        controls={},
        adapter_config={
            "entity_id": "light.corridor",
        },
    )

    assert device.adapter_config == {
        "entity_id": "light.corridor",
    }

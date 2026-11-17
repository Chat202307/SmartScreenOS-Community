import pytest

from src.smartscreen_platform.device_control.model import (
    DeviceControlBinding,
    DeviceControlDefinition,
)
from src.smartscreen_platform.device_control.registry import (
    DeviceControlRegistry,
    DeviceControlRegistryError,
)


def create_binding(
    *,
    device_id="device-1",
    adapter_id="adapter-1",
    control_id="power",
):
    return DeviceControlBinding(
        device_id=device_id,
        adapter_id=adapter_id,
        control=DeviceControlDefinition(
            control_id=control_id,
            kind="boolean",
            parameter=control_id,
        ),
    )


def test_registry_resolves_device_control():
    binding = create_binding()

    registry = DeviceControlRegistry(
        bindings=[binding],
    )

    assert (
        registry.resolve(
            device_id="device-1",
            control_id="power",
        )
        == binding
    )


def test_registry_returns_none_for_unknown_control():
    registry = DeviceControlRegistry(
        bindings=[
            create_binding(),
        ],
    )

    assert (
        registry.resolve(
            device_id="device-1",
            control_id="mode",
        )
        is None
    )


def test_registry_lists_controls_for_device():
    power = create_binding(
        control_id="power",
    )
    mode = create_binding(
        control_id="mode",
    )

    registry = DeviceControlRegistry(
        bindings=[
            mode,
            power,
        ],
    )

    assert registry.for_device(
        "device-1"
    ) == [
        mode,
        power,
    ]


def test_registry_rejects_duplicate_control():
    binding = create_binding()

    with pytest.raises(
        DeviceControlRegistryError
    ):
        DeviceControlRegistry(
            bindings=[
                binding,
                binding,
            ],
        )


def test_registry_requires_bindings():
    with pytest.raises(TypeError):
        DeviceControlRegistry(
            bindings=[
                object(),
            ],
        )

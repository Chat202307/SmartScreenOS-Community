import pytest

from src.smartscreen_platform.device_control.model import (
    DeviceControlDefinition,
)


def test_device_control_definition():
    control = DeviceControlDefinition(
        control_id="power",
        kind="boolean",
        parameter="power",
    )

    assert control.control_id == "power"
    assert control.kind == "boolean"
    assert control.parameter == "power"
    assert control.options == ()


def test_device_control_definition_supports_options():
    control = DeviceControlDefinition(
        control_id="mode",
        kind="enum",
        parameter="mode",
        options=(
            "smart",
            "sleep",
        ),
    )

    assert control.options == (
        "smart",
        "sleep",
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("control_id", ""),
        ("kind", ""),
        ("parameter", ""),
    ],
)
def test_device_control_definition_requires_identity_fields(
    field,
    value,
):
    kwargs = {
        "control_id": "power",
        "kind": "boolean",
        "parameter": "power",
    }

    kwargs[field] = value

    with pytest.raises(ValueError):
        DeviceControlDefinition(
            **kwargs
        )


def test_device_control_definition_copies_options():
    options = [
        "smart",
        "sleep",
    ]

    control = DeviceControlDefinition(
        control_id="mode",
        kind="enum",
        parameter="mode",
        options=options,
    )

    options.append("manual")

    assert control.options == (
        "smart",
        "sleep",
    )

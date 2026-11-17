import pytest

from src.smartscreen_display.xingoo_device_controller import (
    XingooDeviceController,
    XingooDeviceControllerError,
)


DEVICE_ID = "living.air_1"
IOT_ID = "iot-123"


class FakeClient:
    def __init__(self):
        self.calls = []

    def set_power(
        self,
        *,
        iot_id,
        on,
    ):
        self.calls.append(
            {
                "method": "set_power",
                "iot_id": iot_id,
                "on": on,
            }
        )

        return "command-power"

    def send_command(
        self,
        *,
        iot_id,
        command,
    ):
        self.calls.append(
            {
                "method": "send_command",
                "iot_id": iot_id,
                "command": command,
            }
        )

        return "command-control"


def make_controller():
    client = FakeClient()

    controller = XingooDeviceController(
        client=client,
        device_iot_ids={
            DEVICE_ID: IOT_ID,
        },
    )

    return controller, client


def test_controller_turns_device_on():
    controller, client = (
        make_controller()
    )

    result = controller.turn_on(
        DEVICE_ID
    )

    assert result == "command-power"

    assert client.calls == [
        {
            "method": "set_power",
            "iot_id": IOT_ID,
            "on": True,
        }
    ]


def test_controller_turns_device_off():
    controller, client = (
        make_controller()
    )

    result = controller.turn_off(
        DEVICE_ID
    )

    assert result == "command-power"

    assert client.calls == [
        {
            "method": "set_power",
            "iot_id": IOT_ID,
            "on": False,
        }
    ]


def test_controller_sets_smart_mode():
    controller, client = (
        make_controller()
    )

    controller.set_smart_mode(
        DEVICE_ID
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": IOT_ID,
            "command": {
                "WorkMode": 0,
            },
        }
    ]


def test_controller_sets_sleep_mode():
    controller, client = (
        make_controller()
    )

    controller.set_sleep_mode(
        DEVICE_ID
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": IOT_ID,
            "command": {
                "WorkMode": 2,
            },
        }
    ]


@pytest.mark.parametrize(
    "speed",
    [
        1,
        2,
        3,
        4,
        5,
    ],
)
def test_controller_sets_wind_speed(
    speed,
):
    controller, client = (
        make_controller()
    )

    controller.set_wind_speed(
        DEVICE_ID,
        speed,
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": IOT_ID,
            "command": {
                "WindSpeed": speed,
            },
        }
    ]


@pytest.mark.parametrize(
    "speed",
    [
        0,
        6,
        -1,
        1.5,
        "3",
        True,
        None,
    ],
)
def test_controller_rejects_invalid_wind_speed(
    speed,
):
    controller, _ = (
        make_controller()
    )

    with pytest.raises(
        XingooDeviceControllerError,
        match="wind speed",
    ):
        controller.set_wind_speed(
            DEVICE_ID,
            speed,
        )


@pytest.mark.parametrize(
    (
        "method_name",
        "property_name",
    ),
    [
        (
            "set_ions",
            "IonsSwitch",
        ),
        (
            "set_disinfection",
            "DisinfectSwitch",
        ),
        (
            "set_child_lock",
            "ChildLockSwitch",
        ),
    ],
)
@pytest.mark.parametrize(
    "enabled",
    [
        True,
        False,
    ],
)
def test_controller_sets_boolean_controls(
    method_name,
    property_name,
    enabled,
):
    controller, client = (
        make_controller()
    )

    method = getattr(
        controller,
        method_name,
    )

    method(
        DEVICE_ID,
        enabled,
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": IOT_ID,
            "command": {
                property_name:
                    1 if enabled else 0,
            },
        }
    ]


def test_controller_screen_on_uses_inverted_m8_value():
    controller, client = (
        make_controller()
    )

    controller.set_screen_on(
        DEVICE_ID,
        True,
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": IOT_ID,
            "command": {
                "ScreenSwitch": 0,
            },
        }
    ]


def test_controller_screen_off_uses_inverted_m8_value():
    controller, client = (
        make_controller()
    )

    controller.set_screen_on(
        DEVICE_ID,
        False,
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": IOT_ID,
            "command": {
                "ScreenSwitch": 1,
            },
        }
    ]


@pytest.mark.parametrize(
    "method_name",
    [
        "set_ions",
        "set_disinfection",
        "set_screen_on",
        "set_child_lock",
    ],
)
def test_controller_rejects_non_boolean_control_values(
    method_name,
):
    controller, _ = (
        make_controller()
    )

    method = getattr(
        controller,
        method_name,
    )

    with pytest.raises(
        XingooDeviceControllerError,
    ):
        method(
            DEVICE_ID,
            1,
        )


def test_controller_rejects_unknown_device():
    controller, _ = (
        make_controller()
    )

    with pytest.raises(
        XingooDeviceControllerError,
        match="unknown xingoo device",
    ):
        controller.turn_on(
            "bedroom.air_1"
        )


def test_controller_rejects_empty_mapping():
    with pytest.raises(
        XingooDeviceControllerError,
    ):
        XingooDeviceController(
            client=FakeClient(),
            device_iot_ids={},
        )


def test_m8_mode_commands_do_not_emulate_device_side_linked_behavior():
    client = FakeClient()

    controller = XingooDeviceController(
        client=client,
        device_iot_ids={
            "device-1": "iot-123",
        },
    )

    controller.set_smart_mode(
        "device-1"
    )

    controller.set_sleep_mode(
        "device-1"
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": "iot-123",
            "command": {
                "WorkMode": 0,
            },
        },
        {
            "method": "send_command",
            "iot_id": "iot-123",
            "command": {
                "WorkMode": 2,
            },
        },
    ]


def test_m8_wind_speed_command_does_not_force_work_mode():
    client = FakeClient()

    controller = XingooDeviceController(
        client=client,
        device_iot_ids={
            "device-1": "iot-123",
        },
    )

    controller.set_wind_speed(
        "device-1",
        3,
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": "iot-123",
            "command": {
                "WindSpeed": 3,
            },
        },
    ]


def test_m8_independent_controls_send_only_their_own_property():
    client = FakeClient()

    controller = XingooDeviceController(
        client=client,
        device_iot_ids={
            "device-1": "iot-123",
        },
    )

    controller.set_ions(
        "device-1",
        True,
    )
    controller.set_disinfection(
        "device-1",
        True,
    )
    controller.set_child_lock(
        "device-1",
        True,
    )

    assert client.calls == [
        {
            "method": "send_command",
            "iot_id": "iot-123",
            "command": {
                "IonsSwitch": 1,
            },
        },
        {
            "method": "send_command",
            "iot_id": "iot-123",
            "command": {
                "DisinfectSwitch": 1,
            },
        },
        {
            "method": "send_command",
            "iot_id": "iot-123",
            "command": {
                "ChildLockSwitch": 1,
            },
        },
    ]

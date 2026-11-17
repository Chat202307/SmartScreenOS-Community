import pytest

from src.smartscreen_display.xingoo_device_control_executor import (
    XingooDeviceControlExecutor,
    XingooDeviceControlExecutorError,
)
from src.smartscreen_platform.device_control.model import (
    DeviceControlBinding,
    DeviceControlDefinition,
)


DEVICE_ID = "xingoo_test_device_1"


class FakeController:
    def __init__(self):
        self.calls = []

    def turn_on(
        self,
        device_id,
    ):
        self.calls.append(
            (
                "turn_on",
                device_id,
            )
        )
        return "power-on"

    def turn_off(
        self,
        device_id,
    ):
        self.calls.append(
            (
                "turn_off",
                device_id,
            )
        )
        return "power-off"

    def set_smart_mode(
        self,
        device_id,
    ):
        self.calls.append(
            (
                "set_smart_mode",
                device_id,
            )
        )
        return "smart"

    def set_sleep_mode(
        self,
        device_id,
    ):
        self.calls.append(
            (
                "set_sleep_mode",
                device_id,
            )
        )
        return "sleep"

    def set_wind_speed(
        self,
        device_id,
        speed,
    ):
        self.calls.append(
            (
                "set_wind_speed",
                device_id,
                speed,
            )
        )
        return "speed"

    def set_ions(
        self,
        device_id,
        enabled,
    ):
        self.calls.append(
            (
                "set_ions",
                device_id,
                enabled,
            )
        )
        return "ions"

    def set_disinfection(
        self,
        device_id,
        enabled,
    ):
        self.calls.append(
            (
                "set_disinfection",
                device_id,
                enabled,
            )
        )
        return "disinfection"

    def set_screen_on(
        self,
        device_id,
        enabled,
    ):
        self.calls.append(
            (
                "set_screen_on",
                device_id,
                enabled,
            )
        )
        return "screen"

    def set_child_lock(
        self,
        device_id,
        enabled,
    ):
        self.calls.append(
            (
                "set_child_lock",
                device_id,
                enabled,
            )
        )
        return "lock"


def binding(
    control_id,
    *,
    kind="boolean",
    parameter=None,
    options=(),
):
    return DeviceControlBinding(
        device_id=DEVICE_ID,
        adapter_id="xingoo",
        control=DeviceControlDefinition(
            control_id=control_id,
            kind=kind,
            parameter=(
                parameter
                if parameter is not None
                else control_id
            ),
            options=options,
        ),
    )


@pytest.mark.parametrize(
    (
        "value",
        "expected_call",
        "expected_result",
    ),
    [
        (
            True,
            (
                "turn_on",
                DEVICE_ID,
            ),
            "power-on",
        ),
        (
            False,
            (
                "turn_off",
                DEVICE_ID,
            ),
            "power-off",
        ),
    ],
)
def test_executor_maps_power(
    value,
    expected_call,
    expected_result,
):
    controller = FakeController()
    executor = XingooDeviceControlExecutor(
        controller=controller
    )

    result = executor.execute(
        binding=binding("power"),
        value=value,
    )

    assert result == expected_result
    assert controller.calls == [
        expected_call
    ]


@pytest.mark.parametrize(
    (
        "value",
        "expected_call",
    ),
    [
        (
            "smart",
            (
                "set_smart_mode",
                DEVICE_ID,
            ),
        ),
        (
            "sleep",
            (
                "set_sleep_mode",
                DEVICE_ID,
            ),
        ),
    ],
)
def test_executor_maps_mode(
    value,
    expected_call,
):
    controller = FakeController()
    executor = XingooDeviceControlExecutor(
        controller=controller
    )

    executor.execute(
        binding=binding(
            "mode",
            kind="select",
            options=(
                "smart",
                "sleep",
            ),
        ),
        value=value,
    )

    assert controller.calls == [
        expected_call
    ]


@pytest.mark.parametrize(
    "value",
    [
        "1",
        "3",
        "5",
    ],
)
def test_executor_maps_wind_speed_to_integer(
    value,
):
    controller = FakeController()
    executor = XingooDeviceControlExecutor(
        controller=controller
    )

    executor.execute(
        binding=binding(
            "wind_speed",
            kind="select",
            options=(
                "1",
                "2",
                "3",
                "4",
                "5",
            ),
        ),
        value=value,
    )

    assert controller.calls == [
        (
            "set_wind_speed",
            DEVICE_ID,
            int(value),
        )
    ]


@pytest.mark.parametrize(
    (
        "control_id",
        "method_name",
    ),
    [
        (
            "ions",
            "set_ions",
        ),
        (
            "disinfection",
            "set_disinfection",
        ),
        (
            "screen_on",
            "set_screen_on",
        ),
        (
            "child_lock",
            "set_child_lock",
        ),
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
    ],
)
def test_executor_maps_boolean_features(
    control_id,
    method_name,
    value,
):
    controller = FakeController()
    executor = XingooDeviceControlExecutor(
        controller=controller
    )

    executor.execute(
        binding=binding(
            control_id
        ),
        value=value,
    )

    assert controller.calls == [
        (
            method_name,
            DEVICE_ID,
            value,
        )
    ]


def test_executor_rejects_wrong_adapter():
    controller = FakeController()
    executor = XingooDeviceControlExecutor(
        controller=controller
    )

    wrong_binding = DeviceControlBinding(
        device_id=DEVICE_ID,
        adapter_id="other",
        control=DeviceControlDefinition(
            control_id="power",
            kind="boolean",
            parameter="power",
        ),
    )

    with pytest.raises(
        XingooDeviceControlExecutorError,
        match="adapter",
    ):
        executor.execute(
            binding=wrong_binding,
            value=True,
        )


def test_executor_rejects_unknown_control():
    controller = FakeController()
    executor = XingooDeviceControlExecutor(
        controller=controller
    )

    with pytest.raises(
        XingooDeviceControlExecutorError,
        match="unsupported",
    ):
        executor.execute(
            binding=binding(
                "unknown"
            ),
            value=True,
        )

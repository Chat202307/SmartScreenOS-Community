import pytest

from src.smartscreen_platform.device_control.dispatcher import (
    DeviceControlDispatcher,
    DeviceControlDispatcherError,
)
from src.smartscreen_platform.device_control.model import (
    DeviceControlBinding,
    DeviceControlDefinition,
)
from src.smartscreen_platform.device_control.registry import (
    DeviceControlRegistry,
)


DEVICE_ID = "open_public_area.air_purifier_1"


def create_registry():
    return DeviceControlRegistry(
        bindings=[
            DeviceControlBinding(
                device_id=DEVICE_ID,
                adapter_id="xingoo",
                control=DeviceControlDefinition(
                    control_id="power",
                    kind="boolean",
                    parameter="power",
                ),
            ),
            DeviceControlBinding(
                device_id=DEVICE_ID,
                adapter_id="xingoo",
                control=DeviceControlDefinition(
                    control_id="mode",
                    kind="select",
                    parameter="mode",
                    options=(
                        "smart",
                        "sleep",
                    ),
                ),
            ),
            DeviceControlBinding(
                device_id=DEVICE_ID,
                adapter_id="xingoo",
                control=DeviceControlDefinition(
                    control_id="wind_speed",
                    kind="select",
                    parameter="wind_speed",
                    options=(
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                    ),
                ),
            ),
        ]
    )


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def execute(
        self,
        *,
        binding,
        value,
    ):
        self.calls.append(
            (
                binding.device_id,
                binding.control.control_id,
                value,
            )
        )

        return "command-result"


def create_dispatcher(
    *,
    executors=None,
):
    return DeviceControlDispatcher(
        registry=create_registry(),
        executors=(
            executors
            if executors is not None
            else {
                "xingoo": FakeExecutor(),
            }
        ),
    )


def test_dispatcher_resolves_control_and_executes_adapter():
    executor = FakeExecutor()

    dispatcher = create_dispatcher(
        executors={
            "xingoo": executor,
        }
    )

    result = dispatcher.execute(
        device_id=DEVICE_ID,
        control_id="power",
        value=True,
    )

    assert result == "command-result"

    assert executor.calls == [
        (
            DEVICE_ID,
            "power",
            True,
        )
    ]


def test_dispatcher_passes_select_value_to_executor():
    executor = FakeExecutor()

    dispatcher = create_dispatcher(
        executors={
            "xingoo": executor,
        }
    )

    dispatcher.execute(
        device_id=DEVICE_ID,
        control_id="mode",
        value="sleep",
    )

    assert executor.calls == [
        (
            DEVICE_ID,
            "mode",
            "sleep",
        )
    ]


def test_dispatcher_rejects_unknown_device_control():
    dispatcher = create_dispatcher()

    with pytest.raises(
        DeviceControlDispatcherError,
        match="unknown device control",
    ):
        dispatcher.execute(
            device_id=DEVICE_ID,
            control_id="unknown",
            value=True,
        )


def test_dispatcher_rejects_missing_adapter_executor():
    dispatcher = create_dispatcher(
        executors={}
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="executor unavailable",
    ):
        dispatcher.execute(
            device_id=DEVICE_ID,
            control_id="power",
            value=True,
        )


def test_dispatcher_requires_executor_execute_method():
    dispatcher = create_dispatcher(
        executors={
            "xingoo": object(),
        }
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="invalid executor",
    ):
        dispatcher.execute(
            device_id=DEVICE_ID,
            control_id="power",
            value=True,
        )


def test_dispatcher_validates_boolean_control():
    dispatcher = create_dispatcher()

    with pytest.raises(
        DeviceControlDispatcherError,
        match="boolean",
    ):
        dispatcher.execute(
            device_id=DEVICE_ID,
            control_id="power",
            value=1,
        )


def test_dispatcher_validates_select_control():
    dispatcher = create_dispatcher()

    with pytest.raises(
        DeviceControlDispatcherError,
        match="allowed option",
    ):
        dispatcher.execute(
            device_id=DEVICE_ID,
            control_id="mode",
            value="turbo",
        )


def test_dispatcher_accepts_configured_select_option():
    executor = FakeExecutor()

    dispatcher = create_dispatcher(
        executors={
            "xingoo": executor,
        }
    )

    dispatcher.execute(
        device_id=DEVICE_ID,
        control_id="wind_speed",
        value="5",
    )

    assert executor.calls == [
        (
            DEVICE_ID,
            "wind_speed",
            "5",
        )
    ]


def test_dispatcher_accepts_number_control_value():
    binding = DeviceControlBinding(
        device_id="study.light_1",
        adapter_id="fake",
        control=DeviceControlDefinition(
            control_id="brightness",
            parameter="brightness",
            kind="number",
            minimum=0,
            maximum=100,
            step=1,
        ),
    )

    registry = DeviceControlRegistry(
        bindings=[binding]
    )

    class FakeExecutor:
        def __init__(self):
            self.calls = []

        def execute(
            self,
            *,
            binding,
            value,
        ):
            self.calls.append(
                (
                    binding,
                    value,
                )
            )
            return "ok"

    executor = FakeExecutor()

    dispatcher = DeviceControlDispatcher(
        registry=registry,
        executors={
            "fake": executor,
        },
    )

    result = dispatcher.execute(
        device_id="study.light_1",
        control_id="brightness",
        value=50,
    )

    assert result == "ok"
    assert executor.calls == [
        (
            binding,
            50,
        )
    ]


@pytest.mark.parametrize(
    "value",
    [
        -1,
        101,
        True,
        "50",
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_dispatcher_rejects_invalid_number_control_value(
    value,
):
    binding = DeviceControlBinding(
        device_id="study.light_1",
        adapter_id="fake",
        control=DeviceControlDefinition(
            control_id="brightness",
            parameter="brightness",
            kind="number",
            minimum=0,
            maximum=100,
            step=1,
        ),
    )

    registry = DeviceControlRegistry(
        bindings=[binding]
    )

    class FakeExecutor:
        def execute(
            self,
            *,
            binding,
            value,
        ):
            raise AssertionError(
                "invalid value reached executor"
            )

    dispatcher = DeviceControlDispatcher(
        registry=registry,
        executors={
            "fake": FakeExecutor(),
        },
    )

    with pytest.raises(
        DeviceControlDispatcherError
    ):
        dispatcher.execute(
            device_id="study.light_1",
            control_id="brightness",
            value=value,
        )


def test_dispatcher_enforces_number_step():
    binding = DeviceControlBinding(
        device_id="study.light_1",
        adapter_id="fake",
        control=DeviceControlDefinition(
            control_id="color_temperature",
            parameter="color_temperature",
            kind="number",
            minimum=3000,
            maximum=5700,
            step=100,
        ),
    )

    registry = DeviceControlRegistry(
        bindings=[binding]
    )

    class FakeExecutor:
        def execute(
            self,
            *,
            binding,
            value,
        ):
            raise AssertionError(
                "invalid step reached executor"
            )

    dispatcher = DeviceControlDispatcher(
        registry=registry,
        executors={
            "fake": FakeExecutor(),
        },
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="does not match step",
    ):
        dispatcher.execute(
            device_id="study.light_1",
            control_id="color_temperature",
            value=4350,
        )



def make_dispatcher_for_control(control):
    binding = DeviceControlBinding(
        device_id="vacuum_001",
        adapter_id="fake",
        control=control,
    )

    registry = DeviceControlRegistry(
        bindings=[binding]
    )

    executor = FakeExecutor()

    dispatcher = DeviceControlDispatcher(
        registry=registry,
        executors={
            "fake": executor,
        },
    )

    return dispatcher, executor


def test_dispatcher_accepts_action_control():
    dispatcher, executor = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_all",
                kind="action",
                parameter="clean_all",
            )
        )
    )

    result = dispatcher.execute(
        device_id="vacuum_001",
        control_id="clean_all",
        value=None,
    )

    assert result == "command-result"
    assert executor.calls == [
        (
            "vacuum_001",
            "clean_all",
            None,
        )
    ]


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        0,
        1,
        "",
        "run",
        [],
        {},
    ],
)
def test_dispatcher_rejects_action_value(
    value,
):
    dispatcher, _ = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_all",
                kind="action",
                parameter="clean_all",
            )
        )
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="action",
    ):
        dispatcher.execute(
            device_id="vacuum_001",
            control_id="clean_all",
            value=value,
        )


def test_dispatcher_accepts_multi_select_control():
    dispatcher, executor = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_areas",
                kind="multi_select",
                parameter="clean_areas",
                options=(
                    "living",
                    "dining",
                    "study",
                ),
            )
        )
    )

    result = dispatcher.execute(
        device_id="vacuum_001",
        control_id="clean_areas",
        value=[
            "living",
            "study",
        ],
    )

    assert result == "command-result"
    assert executor.calls == [
        (
            "vacuum_001",
            "clean_areas",
            [
                "living",
                "study",
            ],
        )
    ]


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "living",
        (),
        {},
        1,
        True,
    ],
)
def test_dispatcher_rejects_non_list_multi_select_value(
    value,
):
    dispatcher, _ = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_areas",
                kind="multi_select",
                parameter="clean_areas",
                options=(
                    "living",
                    "dining",
                    "study",
                ),
            )
        )
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="multi_select",
    ):
        dispatcher.execute(
            device_id="vacuum_001",
            control_id="clean_areas",
            value=value,
        )


def test_dispatcher_rejects_empty_multi_select_value():
    dispatcher, _ = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_areas",
                kind="multi_select",
                parameter="clean_areas",
                options=(
                    "living",
                    "dining",
                    "study",
                ),
            )
        )
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="at least one",
    ):
        dispatcher.execute(
            device_id="vacuum_001",
            control_id="clean_areas",
            value=[],
        )


def test_dispatcher_rejects_unknown_multi_select_option():
    dispatcher, _ = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_areas",
                kind="multi_select",
                parameter="clean_areas",
                options=(
                    "living",
                    "dining",
                    "study",
                ),
            )
        )
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="allowed option",
    ):
        dispatcher.execute(
            device_id="vacuum_001",
            control_id="clean_areas",
            value=[
                "living",
                "kitchen",
            ],
        )


def test_dispatcher_rejects_duplicate_multi_select_option():
    dispatcher, _ = (
        make_dispatcher_for_control(
            DeviceControlDefinition(
                control_id="clean_areas",
                kind="multi_select",
                parameter="clean_areas",
                options=(
                    "living",
                    "dining",
                    "study",
                ),
            )
        )
    )

    with pytest.raises(
        DeviceControlDispatcherError,
        match="duplicate",
    ):
        dispatcher.execute(
            device_id="vacuum_001",
            control_id="clean_areas",
            value=[
                "living",
                "living",
            ],
        )

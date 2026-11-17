import pytest

from src.smartscreen_display.home_assistant_device_control_executor import (
    HomeAssistantDeviceControlExecutor,
    HomeAssistantDeviceControlExecutorError,
)
from src.smartscreen_platform.device_control import (
    DeviceControlBinding,
    DeviceControlDefinition,
)


DEVICE_ID = "corridor.light_1"
ENTITY_ID = (
    'light.demo_entity_026'
)


class FakeClient:
    def __init__(self):
        self.calls = []

    def call_service(
        self,
        domain,
        service,
        entity_id,
        *,
        service_data=None,
    ):
        self.calls.append(
            (
                domain,
                service,
                entity_id,
                service_data,
            )
        )

        return {
            "ok": True,
        }


def make_binding(
    *,
    adapter_id="home_assistant",
    control_id="power",
):
    return DeviceControlBinding(
        device_id=DEVICE_ID,
        adapter_id=adapter_id,
        control=DeviceControlDefinition(
            control_id=control_id,
            parameter="power",
            kind="boolean",
        ),
    )


def make_executor():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                DEVICE_ID: ENTITY_ID,
            },
        )
    )

    return executor, client


def test_executor_has_home_assistant_adapter_id():
    assert (
        HomeAssistantDeviceControlExecutor
        .ADAPTER_ID
        == "home_assistant"
    )


def test_executor_turns_light_on():
    executor, client = make_executor()

    result = executor.execute(
        binding=make_binding(),
        value=True,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "light",
            "turn_on",
            ENTITY_ID,
            None,
        )
    ]


def test_executor_turns_light_off():
    executor, client = make_executor()

    executor.execute(
        binding=make_binding(),
        value=False,
    )

    assert client.calls == [
        (
            "light",
            "turn_off",
            ENTITY_ID,
            None,
        )
    ]


def test_executor_resolves_entity_from_device_id():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                "living.light_1":
                    "light.living",
                "corridor.light_1":
                    "light.corridor",
            },
        )
    )

    binding = DeviceControlBinding(
        device_id="living.light_1",
        adapter_id="home_assistant",
        control=DeviceControlDefinition(
            control_id="power",
            parameter="power",
            kind="boolean",
        ),
    )

    executor.execute(
        binding=binding,
        value=True,
    )

    assert client.calls == [
        (
            "light",
            "turn_on",
            "light.living",
            None,
        )
    ]


def test_executor_rejects_unknown_device():
    executor, _ = make_executor()

    binding = DeviceControlBinding(
        device_id="unknown.light",
        adapter_id="home_assistant",
        control=DeviceControlDefinition(
            control_id="power",
            parameter="power",
            kind="boolean",
        ),
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="unknown home assistant device",
    ):
        executor.execute(
            binding=binding,
            value=True,
        )


def test_executor_rejects_wrong_adapter():
    executor, _ = make_executor()

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="unsupported adapter",
    ):
        executor.execute(
            binding=make_binding(
                adapter_id="xingoo",
            ),
            value=True,
        )


def test_executor_rejects_unsupported_control():
    executor, _ = make_executor()

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="unsupported home assistant control",
    ):
        executor.execute(
            binding=make_binding(
                control_id="unsupported_control",
            ),
            value=True,
        )


def test_executor_rejects_non_boolean_power_value():
    executor, _ = make_executor()

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="power value must be boolean",
    ):
        executor.execute(
            binding=make_binding(),
            value="true",
        )


def test_executor_rejects_invalid_entity_id():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                DEVICE_ID: "invalid-entity",
            },
        )
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="invalid home assistant entity",
    ):
        executor.execute(
            binding=make_binding(),
            value=True,
        )


def test_executor_requires_device_mapping():
    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="device mapping must not be empty",
    ):
        HomeAssistantDeviceControlExecutor(
            client=FakeClient(),
            device_entity_ids={},
        )


def test_executor_turns_switch_on_and_off():
    entity_id = "switch.master_bath_makeup"

    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                DEVICE_ID: entity_id,
            },
        )
    )

    executor.execute(
        binding=make_binding(),
        value=True,
    )

    executor.execute(
        binding=make_binding(),
        value=False,
    )

    assert client.calls == [
        (
            "switch",
            "turn_on",
            entity_id,
            None,
        ),
        (
            "switch",
            "turn_off",
            entity_id,
            None,
        ),
    ]


CLIMATE_DEVICE_ID = "study.air_conditioner_1"
CLIMATE_ENTITY_ID = (
    "climate."
    "dnake_ben_di_she_bei_"
    "shu_fang_kong_diao"
)


def make_climate_binding(
    control_id,
    *,
    kind="select",
    options=(),
):
    return DeviceControlBinding(
        device_id=CLIMATE_DEVICE_ID,
        adapter_id="home_assistant",
        control=DeviceControlDefinition(
            control_id=control_id,
            parameter=control_id,
            kind=kind,
            options=options,
        ),
    )


def make_climate_executor():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                CLIMATE_DEVICE_ID:
                    CLIMATE_ENTITY_ID,
            },
        )
    )

    return executor, client


def test_executor_sets_climate_operating_state():
    executor, client = (
        make_climate_executor()
    )

    result = executor.execute(
        binding=make_climate_binding(
            "operating_state",
            options=(
                "off",
                "cool",
                "heat",
            ),
        ),
        value="heat",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "climate",
            "set_hvac_mode",
            CLIMATE_ENTITY_ID,
            {
                "hvac_mode": "heat",
            },
        )
    ]


def test_executor_sets_climate_target_temperature():
    executor, client = (
        make_climate_executor()
    )

    executor.execute(
        binding=make_climate_binding(
            "target_temperature",
            options=tuple(
                str(value)
                for value in range(
                    16,
                    31,
                )
            ),
        ),
        value="24",
    )

    assert client.calls == [
        (
            "climate",
            "set_temperature",
            CLIMATE_ENTITY_ID,
            {
                "temperature": 24.0,
            },
        )
    ]


def test_executor_sets_climate_fan_mode():
    executor, client = (
        make_climate_executor()
    )

    executor.execute(
        binding=make_climate_binding(
            "fan_mode",
            options=(
                "low",
                "medium",
            ),
        ),
        value="medium",
    )

    assert client.calls == [
        (
            "climate",
            "set_fan_mode",
            CLIMATE_ENTITY_ID,
            {
                "fan_mode": "medium",
            },
        )
    ]


def test_executor_rejects_climate_control_for_non_climate_entity():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                CLIMATE_DEVICE_ID:
                    "light.study",
            },
        )
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="climate control requires climate entity",
    ):
        executor.execute(
            binding=make_climate_binding(
                "fan_mode",
                options=(
                    "low",
                    "medium",
                ),
            ),
            value="low",
        )


COVER_DEVICE_ID = "princess_room.curtain_1"
COVER_ENTITY_ID = (
    'cover.demo_entity_019'
)


def make_cover_binding(
    control_id,
    *,
    kind="select",
    options=(),
):
    return DeviceControlBinding(
        device_id=COVER_DEVICE_ID,
        adapter_id="home_assistant",
        control=DeviceControlDefinition(
            control_id=control_id,
            parameter=control_id,
            kind=kind,
            options=options,
        ),
    )


def make_cover_executor():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                COVER_DEVICE_ID:
                    COVER_ENTITY_ID,
            },
        )
    )

    return executor, client


@pytest.mark.parametrize(
    (
        "value",
        "service",
    ),
    [
        (
            "open",
            "open_cover",
        ),
        (
            "close",
            "close_cover",
        ),
        (
            "stop",
            "stop_cover",
        ),
    ],
)
def test_executor_controls_cover_state(
    value,
    service,
):
    executor, client = (
        make_cover_executor()
    )

    result = executor.execute(
        binding=make_cover_binding(
            "state",
            options=(
                "open",
                "close",
                "stop",
            ),
        ),
        value=value,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "cover",
            service,
            COVER_ENTITY_ID,
            None,
        )
    ]


def test_executor_sets_cover_position():
    executor, client = (
        make_cover_executor()
    )

    result = executor.execute(
        binding=make_cover_binding(
            "position",
            kind="select",
            options=tuple(
                str(value)
                for value in range(
                    0,
                    101,
                )
            ),
        ),
        value="37",
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "cover",
            "set_cover_position",
            COVER_ENTITY_ID,
            {
                "position": 37,
            },
        )
    ]


@pytest.mark.parametrize(
    "value",
    [
        -1,
        101,
    ],
)
def test_executor_rejects_cover_position_outside_percent_range(
    value,
):
    executor, _ = (
        make_cover_executor()
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="cover position must be between 0 and 100",
    ):
        executor.execute(
            binding=make_cover_binding(
                "position",
            ),
            value=value,
        )


def test_executor_rejects_unknown_cover_state():
    executor, _ = (
        make_cover_executor()
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="unsupported cover state",
    ):
        executor.execute(
            binding=make_cover_binding(
                "state",
            ),
            value="opening",
        )


def test_executor_rejects_cover_control_for_non_cover_entity():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                COVER_DEVICE_ID:
                    "light.princess_room",
            },
        )
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="cover control requires cover entity",
    ):
        executor.execute(
            binding=make_cover_binding(
                "state",
            ),
            value="open",
        )


SMART_LIGHT_DEVICE_ID = "study.ceiling_light_1"
SMART_LIGHT_ENTITY_ID = (
    "light.demo_entity_029"
)


def make_smart_light_binding(
    control_id,
):
    return DeviceControlBinding(
        device_id=SMART_LIGHT_DEVICE_ID,
        adapter_id="home_assistant",
        control=DeviceControlDefinition(
            control_id=control_id,
            parameter=control_id,
            kind="number",
        ),
    )


def make_smart_light_executor():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                SMART_LIGHT_DEVICE_ID:
                    SMART_LIGHT_ENTITY_ID,
            },
        )
    )

    return executor, client


def test_executor_sets_light_brightness_percentage():
    executor, client = (
        make_smart_light_executor()
    )

    executor.execute(
        binding=make_smart_light_binding(
            "brightness"
        ),
        value=50,
    )

    assert client.calls == [
        (
            "light",
            "turn_on",
            SMART_LIGHT_ENTITY_ID,
            {
                "brightness_pct": 50.0,
            },
        )
    ]


def test_executor_sets_light_color_temperature_kelvin():
    executor, client = (
        make_smart_light_executor()
    )

    executor.execute(
        binding=make_smart_light_binding(
            "color_temperature"
        ),
        value=4350,
    )

    assert client.calls == [
        (
            "light",
            "turn_on",
            SMART_LIGHT_ENTITY_ID,
            {
                "color_temp_kelvin": 4350.0,
            },
        )
    ]


@pytest.mark.parametrize(
    "control_id",
    [
        "brightness",
        "color_temperature",
    ],
)
def test_executor_rejects_light_number_control_for_non_light_entity(
    control_id,
):
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                SMART_LIGHT_DEVICE_ID:
                    "switch.not_a_light",
            },
        )
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="light control requires light entity",
    ):
        executor.execute(
            binding=make_smart_light_binding(
                control_id
            ),
            value=50,
        )



VACUUM_DEVICE_ID = "vacuum_001"
VACUUM_ENTITY_ID = "vacuum.demo_entity_064"
VACUUM_CLEAN_ALL_ENTITY_ID = (
    "button.p10_pro_quan_wu_qing_sao"
)


def make_vacuum_binding(
    control_id,
    *,
    kind,
    options=(),
):
    return DeviceControlBinding(
        device_id=VACUUM_DEVICE_ID,
        adapter_id="home_assistant",
        control=DeviceControlDefinition(
            control_id=control_id,
            parameter=control_id,
            kind=kind,
            options=options,
        ),
    )


def make_vacuum_executor():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                VACUUM_DEVICE_ID:
                    VACUUM_ENTITY_ID,
            },
            device_adapter_configs={
                VACUUM_DEVICE_ID: {
                    "entity_id":
                        VACUUM_ENTITY_ID,
                    "clean_all_entity_id":
                        VACUUM_CLEAN_ALL_ENTITY_ID,
                    "cleaning_area_ids": {
                        "living":
                            "sun_da_sheng_ke_ting",
                        "dining":
                            "sun_da_sheng_can_ting",
                        "study":
                            "sun_da_sheng_shu_fang",
                    },
                },
            },
        )
    )

    return executor, client


def test_executor_starts_vacuum_clean_all_action():
    executor, client = make_vacuum_executor()

    result = executor.execute(
        binding=make_vacuum_binding(
            "clean_all",
            kind="action",
        ),
        value=None,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "button",
            "press",
            VACUUM_CLEAN_ALL_ENTITY_ID,
            None,
        )
    ]


def test_executor_starts_vacuum_clean_areas():
    executor, client = make_vacuum_executor()

    result = executor.execute(
        binding=make_vacuum_binding(
            "clean_areas",
            kind="multi_select",
            options=(
                "living",
                "dining",
                "study",
            ),
        ),
        value=[
            "living",
            "study",
        ],
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "vacuum",
            "clean_area",
            VACUUM_ENTITY_ID,
            {
                "cleaning_area_id": [
                    "sun_da_sheng_ke_ting",
                    "sun_da_sheng_shu_fang",
                ],
            },
        )
    ]


def test_executor_rejects_missing_vacuum_clean_all_entity():
    client = FakeClient()

    executor = (
        HomeAssistantDeviceControlExecutor(
            client=client,
            device_entity_ids={
                VACUUM_DEVICE_ID:
                    VACUUM_ENTITY_ID,
            },
            device_adapter_configs={
                VACUUM_DEVICE_ID: {
                    "entity_id":
                        VACUUM_ENTITY_ID,
                },
            },
        )
    )

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="clean_all",
    ):
        executor.execute(
            binding=make_vacuum_binding(
                "clean_all",
                kind="action",
            ),
            value=None,
        )


def test_executor_rejects_unknown_vacuum_cleaning_area():
    executor, _ = make_vacuum_executor()

    with pytest.raises(
        HomeAssistantDeviceControlExecutorError,
        match="cleaning area",
    ):
        executor.execute(
            binding=make_vacuum_binding(
                "clean_areas",
                kind="multi_select",
                options=(
                    "living",
                    "kitchen",
                ),
            ),
            value=[
                "living",
                "kitchen",
            ],
        )


def test_executor_returns_vacuum_to_dock():
    executor, client = make_vacuum_executor()

    result = executor.execute(
        binding=make_vacuum_binding(
            "return_to_dock",
            kind="action",
        ),
        value=None,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "vacuum",
            "return_to_base",
            VACUUM_ENTITY_ID,
            None,
        )
    ]


def test_executor_returns_vacuum_to_dock():
    executor, client = make_vacuum_executor()

    result = executor.execute(
        binding=make_vacuum_binding(
            "return_to_dock",
            kind="action",
        ),
        value=None,
    )

    assert result == {
        "ok": True,
    }

    assert client.calls == [
        (
            "vacuum",
            "return_to_base",
            VACUUM_ENTITY_ID,
            None,
        )
    ]

import pytest

from src.smartscreen_display.home_assistant_device_data import (
    HomeAssistantDeviceDataAdapter,
)
from src.smartscreen_platform.device_data import (
    DeviceDataIngestionService,
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceParameterStore,
    DeviceRegistry,
)


def make_registry():
    return DeviceRegistry(
        devices=[
            DeviceDefinition(
                device_id="living.presence_sensor_1",
                name="客厅人体",
                location_id="living",
                adapter_id="home_assistant",
                parameters={
                    "presence": (
                        DeviceParameterDefinition(
                            parameter="presence",
                            source_id=(
                                "binary_sensor."
                                "living_presence"
                            ),
                            value_type="bool",
                        )
                    ),
                    "illuminance": (
                        DeviceParameterDefinition(
                            parameter="illuminance",
                            source_id=(
                                "sensor."
                                "living_illuminance"
                            ),
                            value_type="float",
                            unit="lux",
                        )
                    ),
                    "motion_idle_seconds": (
                        DeviceParameterDefinition(
                            parameter=(
                                "motion_idle_seconds"
                            ),
                            source_id=(
                                "sensor."
                                "living_motion_idle"
                            ),
                            value_type="int",
                            unit="s",
                        )
                    ),
                },
            )
        ]
    )


def make_adapter():
    registry = make_registry()
    store = DeviceParameterStore(
        registry=registry
    )
    service = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=service,
        ),
        store,
    )


def test_adapter_converts_float_and_ingests():
    adapter, store = make_adapter()

    observation = adapter.ingest_state(
        entity_id="sensor.living_illuminance",
        raw_state="49",
    )

    assert observation.value == 49.0

    entry = store.get(
        "living.presence_sensor_1",
        "illuminance",
    )

    assert entry is not None
    assert entry.value == 49.0


def test_adapter_converts_int_and_ingests():
    adapter, store = make_adapter()

    observation = adapter.ingest_state(
        entity_id="sensor.living_motion_idle",
        raw_state="300",
    )

    assert observation.value == 300
    assert isinstance(
        observation.value,
        int,
    )

    assert store.get(
        "living.presence_sensor_1",
        "motion_idle_seconds",
    ).value == 300


@pytest.mark.parametrize(
    "raw_state,expected",
    [
        ("on", True),
        ("true", True),
        ("1", True),
        ("off", False),
        ("false", False),
        ("0", False),
    ],
)
def test_adapter_converts_bool(
    raw_state,
    expected,
):
    adapter, store = make_adapter()

    observation = adapter.ingest_state(
        entity_id="binary_sensor.living_presence",
        raw_state=raw_state,
    )

    assert observation.value is expected

    assert store.get(
        "living.presence_sensor_1",
        "presence",
    ).value is expected


def test_adapter_marks_unavailable_without_type_conversion():
    adapter, store = make_adapter()

    observation = adapter.ingest_state(
        entity_id="sensor.living_illuminance",
        raw_state="unavailable",
    )

    assert observation.quality == (
        "unavailable"
    )

    entry = store.get(
        "living.presence_sensor_1",
        "illuminance",
    )

    assert entry is not None
    assert entry.available is False
    assert entry.value == "unavailable"


def test_adapter_returns_none_for_unknown_source():
    adapter, _ = make_adapter()

    assert (
        adapter.ingest_state(
            entity_id="sensor.unknown",
            raw_state="49",
        )
        is None
    )


def test_adapter_rejects_invalid_boolean_value():
    adapter, _ = make_adapter()

    with pytest.raises(ValueError):
        adapter.ingest_state(
            entity_id="binary_sensor.living_presence",
            raw_state="maybe",
        )


def make_smart_light_adapter():
    entity_id = (
        "light."
        "gtop_cn_672456192_yl01_s_2_light"
    )

    device = DeviceDefinition(
        device_id="living.main_light_1",
        name="客厅主灯",
        location_id="living",
        adapter_id="home_assistant",
        parameters={
            "power": (
                DeviceParameterDefinition(
                    parameter="power",
                    source_id=(
                        entity_id
                        + "#power"
                    ),
                    value_type="bool",
                )
            ),
            "brightness": (
                DeviceParameterDefinition(
                    parameter="brightness",
                    source_id=(
                        entity_id
                        + "#brightness"
                    ),
                    value_type="int",
                    unit="percent",
                )
            ),
            "color_temperature": (
                DeviceParameterDefinition(
                    parameter="color_temperature",
                    source_id=(
                        entity_id
                        + "#color_temperature"
                    ),
                    value_type="int",
                    unit="K",
                )
            ),
        },
        adapter_config={
            "entity_id": entity_id,
        },
    )

    registry = DeviceRegistry(
        devices=[device]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    ingestion = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_smart_light_state_fans_out_canonical_parameters():
    adapter, store = (
        make_smart_light_adapter()
    )

    observations = adapter.ingest_state(
        entity_id=(
            "light."
            "gtop_cn_672456192_yl01_s_2_light"
        ),
        raw_state={
            "state": "on",
            "attributes": {
                "brightness": 255,
                "color_temp_kelvin": 4350,
            },
        },
    )

    assert len(observations) == 3

    assert (
        store.get(
            "living.main_light_1",
            "power",
        ).value
        is True
    )

    assert (
        store.get(
            "living.main_light_1",
            "brightness",
        ).value
        == 100
    )

    assert (
        store.get(
            "living.main_light_1",
            "color_temperature",
        ).value
        == 4350
    )


def test_smart_light_brightness_is_normalized_to_percent():
    adapter, store = (
        make_smart_light_adapter()
    )

    adapter.ingest_state(
        entity_id=(
            "light."
            "gtop_cn_672456192_yl01_s_2_light"
        ),
        raw_state={
            "state": "on",
            "attributes": {
                "brightness": 128,
                "color_temp_kelvin": 4000,
            },
        },
    )

    assert (
        store.get(
            "living.main_light_1",
            "brightness",
        ).value
        == 50
    )


def test_smart_light_missing_attribute_marks_parameter_unavailable():
    adapter, store = (
        make_smart_light_adapter()
    )

    adapter.ingest_state(
        entity_id=(
            "light."
            "gtop_cn_672456192_yl01_s_2_light"
        ),
        raw_state={
            "state": "on",
            "attributes": {},
        },
    )

    assert (
        store.get(
            "living.main_light_1",
            "power",
        ).value
        is True
    )

    assert (
        store.get(
            "living.main_light_1",
            "brightness",
        ).available
        is False
    )

    assert (
        store.get(
            "living.main_light_1",
            "color_temperature",
        ).available
        is False
    )


def test_regular_source_accepts_full_home_assistant_state():
    adapter, store = make_adapter()

    observation = adapter.ingest_state(
        entity_id="sensor.living_illuminance",
        raw_state={
            "entity_id": (
                "sensor.living_illuminance"
            ),
            "state": "49",
            "attributes": {
                "unit_of_measurement": "lx",
            },
        },
    )

    assert observation.value == 49.0

    assert (
        store.get(
            "living.presence_sensor_1",
            "illuminance",
        ).value
        == 49.0
    )


def make_climate_adapter():
    entity_id = (
        "climate."
        "dnake_ben_di_she_bei_"
        "shu_fang_kong_diao"
    )

    device = DeviceDefinition(
        device_id="study.air_conditioner_1",
        name="书房空调",
        location_id="study",
        adapter_id="home_assistant",
        parameters={
            "operating_state": (
                DeviceParameterDefinition(
                    parameter="operating_state",
                    source_id=(
                        entity_id
                        + "#operating_state"
                    ),
                    value_type="string",
                )
            ),
            "target_temperature": (
                DeviceParameterDefinition(
                    parameter="target_temperature",
                    source_id=(
                        entity_id
                        + "#target_temperature"
                    ),
                    value_type="float",
                    unit="°C",
                )
            ),
            "current_temperature": (
                DeviceParameterDefinition(
                    parameter="current_temperature",
                    source_id=(
                        entity_id
                        + "#current_temperature"
                    ),
                    value_type="float",
                    unit="°C",
                )
            ),
            "fan_mode": (
                DeviceParameterDefinition(
                    parameter="fan_mode",
                    source_id=(
                        entity_id
                        + "#fan_mode"
                    ),
                    value_type="string",
                )
            ),
        },
        adapter_config={
            "entity_id": entity_id,
        },
    )

    registry = DeviceRegistry(
        devices=[device]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    ingestion = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_climate_state_fans_out_canonical_parameters():
    adapter, store = make_climate_adapter()

    observations = adapter.ingest_state(
        entity_id=(
            "climate."
            "dnake_ben_di_she_bei_"
            "shu_fang_kong_diao"
        ),
        raw_state={
            "state": "cool",
            "attributes": {
                "temperature": 24,
                "current_temperature": 28,
                "fan_mode": "low",
            },
        },
    )

    assert len(observations) == 4

    assert (
        store.get(
            "study.air_conditioner_1",
            "operating_state",
        ).value
        == "cool"
    )

    assert (
        store.get(
            "study.air_conditioner_1",
            "target_temperature",
        ).value
        == 24.0
    )

    assert (
        store.get(
            "study.air_conditioner_1",
            "current_temperature",
        ).value
        == 28.0
    )

    assert (
        store.get(
            "study.air_conditioner_1",
            "fan_mode",
        ).value
        == "low"
    )


def test_climate_null_fan_mode_is_unavailable():
    adapter, store = make_climate_adapter()

    adapter.ingest_state(
        entity_id=(
            "climate."
            "dnake_ben_di_she_bei_"
            "shu_fang_kong_diao"
        ),
        raw_state={
            "state": "cool",
            "attributes": {
                "temperature": 24,
                "current_temperature": 28,
                "fan_mode": None,
            },
        },
    )

    fan_mode = store.get(
        "study.air_conditioner_1",
        "fan_mode",
    )

    assert fan_mode.available is False
    assert fan_mode.value is None


def test_climate_unavailable_marks_all_parameters_unavailable():
    adapter, store = make_climate_adapter()

    observations = adapter.ingest_state(
        entity_id=(
            "climate."
            "dnake_ben_di_she_bei_"
            "shu_fang_kong_diao"
        ),
        raw_state={
            "state": "unavailable",
            "attributes": {
                "temperature": 24,
                "current_temperature": 28,
                "fan_mode": "low",
            },
        },
    )

    assert len(observations) == 4

    for parameter in (
        "operating_state",
        "target_temperature",
        "current_temperature",
        "fan_mode",
    ):
        assert (
            store.get(
                "study.air_conditioner_1",
                parameter,
            ).available
            is False
        )


def make_cover_adapter():
    entity_id = (
        'cover.demo_entity_019'
    )

    device = DeviceDefinition(
        device_id="princess_room.curtain_1",
        name="公主房窗帘",
        location_id="princess_room",
        adapter_id="home_assistant",
        parameters={
            "state": (
                DeviceParameterDefinition(
                    parameter="state",
                    source_id=(
                        entity_id
                        + "#state"
                    ),
                    value_type="string",
                )
            ),
            "position": (
                DeviceParameterDefinition(
                    parameter="position",
                    source_id=(
                        entity_id
                        + "#position"
                    ),
                    value_type="int",
                    unit="percent",
                )
            ),
        },
        adapter_config={
            "entity_id": entity_id,
        },
    )

    registry = DeviceRegistry(
        devices=[device]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    ingestion = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_cover_state_fans_out_state_and_position():
    adapter, store = make_cover_adapter()

    observations = adapter.ingest_state(
        entity_id=(
            'cover.demo_entity_019'
        ),
        raw_state={
            "state": "open",
            "attributes": {
                "current_position": 100,
            },
        },
    )

    assert len(observations) == 2

    assert (
        store.get(
            "princess_room.curtain_1",
            "state",
        ).value
        == "open"
    )

    assert (
        store.get(
            "princess_room.curtain_1",
            "position",
        ).value
        == 100
    )


def test_cover_missing_position_marks_position_unavailable():
    adapter, store = make_cover_adapter()

    adapter.ingest_state(
        entity_id=(
            'cover.demo_entity_019'
        ),
        raw_state={
            "state": "open",
            "attributes": {},
        },
    )

    position = store.get(
        "princess_room.curtain_1",
        "position",
    )

    assert position.available is False
    assert position.value is None


def test_cover_unavailable_marks_all_parameters_unavailable():
    adapter, store = make_cover_adapter()

    observations = adapter.ingest_state(
        entity_id=(
            'cover.demo_entity_019'
        ),
        raw_state={
            "state": "unavailable",
            "attributes": {
                "current_position": 100,
            },
        },
    )

    assert len(observations) == 2

    for parameter in (
        "state",
        "position",
    ):
        assert (
            store.get(
                "princess_room.curtain_1",
                parameter,
            ).available
            is False
        )


@pytest.mark.parametrize(
    "position",
    [
        -1,
        101,
    ],
)
def test_cover_rejects_position_outside_percent_range(
    position,
):
    adapter, _ = make_cover_adapter()

    with pytest.raises(
        ValueError,
        match=(
            "invalid home assistant "
            "cover position"
        ),
    ):
        adapter.ingest_state(
            entity_id=(
                'cover.demo_entity_019'
            ),
            raw_state={
                "state": "open",
                "attributes": {
                    "current_position": (
                        position
                    ),
                },
            },
        )




def make_temperature_adapter():
    device = DeviceDefinition(
        device_id="living.temperature_sensor_1",
        name="客厅温度",
        location_id="living",
        adapter_id="home_assistant",
        parameters={
            "temperature": (
                DeviceParameterDefinition(
                    parameter="temperature",
                    source_id=(
                        "sensor.living_temperature"
                    ),
                    value_type="float",
                    unit="°C",
                )
            ),
        },
    )

    registry = DeviceRegistry(
        devices=[device]
    )
    store = DeviceParameterStore(
        registry=registry
    )
    ingestion = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_adapter_converts_fahrenheit_temperature_to_celsius():
    adapter, store = make_temperature_adapter()

    observation = adapter.ingest_state(
        entity_id="sensor.living_temperature",
        raw_state={
            "state": "79.52",
            "attributes": {
                "unit_of_measurement": "°F",
                "device_class": "temperature",
            },
        },
    )

    assert observation.value == pytest.approx(
        26.4
    )
    assert observation.unit == "°C"

    entry = store.get(
        "living.temperature_sensor_1",
        "temperature",
    )

    assert entry.value == pytest.approx(
        26.4
    )
    assert entry.unit == "°C"


def test_adapter_keeps_celsius_temperature_unchanged():
    adapter, store = make_temperature_adapter()

    observation = adapter.ingest_state(
        entity_id="sensor.living_temperature",
        raw_state={
            "state": "26.4",
            "attributes": {
                "unit_of_measurement": "°C",
                "device_class": "temperature",
            },
        },
    )

    assert observation.value == pytest.approx(
        26.4
    )
    assert observation.unit == "°C"

    assert store.get(
        "living.temperature_sensor_1",
        "temperature",
    ).value == pytest.approx(
        26.4
    )




def make_entry_doorbell_adapter():
    device = DeviceDefinition(
        device_id="living.entry_doorbell_1",
        name="入户门门铃",
        location_id="living",
        adapter_id="home_assistant",
        parameters={
            "motion": DeviceParameterDefinition(
                parameter="motion",
                source_id=(
                    "binary_sensor."
                    "madv_cn_1067779402_mi3iot_"
                    "motion_detection_p_10_55"
                ),
                value_type="bool",
            ),
            "battery_level": DeviceParameterDefinition(
                parameter="battery_level",
                source_id=(
                    "sensor."
                    "madv_cn_1067779402_mi3iot_"
                    "battery_level_p_8_1"
                ),
                value_type="float",
                unit="%",
            ),
            "operating_state": DeviceParameterDefinition(
                parameter="operating_state",
                source_id=(
                    "sensor."
                    "madv_cn_1067779402_mi3iot_"
                    "status_p_2_2"
                ),
                value_type="string",
            ),
        },
    )

    registry = DeviceRegistry(
        devices=[device]
    )
    store = DeviceParameterStore(
        registry=registry
    )
    service = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=service,
        ),
        store,
    )


def test_adapter_ingests_real_entry_doorbell_state_sources():
    adapter, store = make_entry_doorbell_adapter()

    motion = adapter.ingest_state(
        entity_id=(
            "binary_sensor."
            "madv_cn_1067779402_mi3iot_"
            "motion_detection_p_10_55"
        ),
        raw_state="off",
    )

    battery = adapter.ingest_state(
        entity_id=(
            "sensor."
            "madv_cn_1067779402_mi3iot_"
            "battery_level_p_8_1"
        ),
        raw_state="4",
    )

    operating_state = adapter.ingest_state(
        entity_id=(
            "sensor."
            "madv_cn_1067779402_mi3iot_"
            "status_p_2_2"
        ),
        raw_state="Idle",
    )

    assert motion.value is False
    assert battery.value == 4.0
    assert battery.unit == "%"
    assert operating_state.value == "Idle"

    assert store.get(
        "living.entry_doorbell_1",
        "motion",
    ).value is False

    assert store.get(
        "living.entry_doorbell_1",
        "battery_level",
    ).value == 4.0

    assert store.get(
        "living.entry_doorbell_1",
        "operating_state",
    ).value == "Idle"

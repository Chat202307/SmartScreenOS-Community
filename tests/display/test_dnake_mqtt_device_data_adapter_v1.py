from src.smartscreen_display.dnake_mqtt_device_data import (
    DnakeMqttDeviceDataAdapter,
)
from src.smartscreen_platform.device_data import (
    DeviceDataIngestionService,
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceParameterStore,
    DeviceRegistry,
)


def _build_adapter():
    device = DeviceDefinition(
        device_id="living.curtain_1",
        name="客厅窗帘",
        location_id="living",
        adapter_id="dnake_mqtt",
        parameters={
            "state": DeviceParameterDefinition(
                parameter="state",
                source_id=(
                    "dnake/curtain/客厅窗帘/state"
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
    ingestion = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    return (
        DnakeMqttDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_maps_open_state_to_canonical_open():
    adapter, store = _build_adapter()

    observation = adapter.ingest_message(
        topic="dnake/curtain/客厅窗帘/state",
        raw_payload="OPEN",
    )

    assert observation.value == "open"
    assert (
        store.get(
            "living.curtain_1",
            "state",
        ).value
        == "open"
    )


def test_maps_close_state_to_canonical_closed():
    adapter, _ = _build_adapter()

    observation = adapter.ingest_message(
        topic="dnake/curtain/客厅窗帘/state",
        raw_payload="CLOSE",
    )

    assert observation.value == "closed"


def test_maps_stopped_state_to_canonical_stopped():
    adapter, _ = _build_adapter()

    observation = adapter.ingest_message(
        topic="dnake/curtain/客厅窗帘/state",
        raw_payload="STOPPED",
    )

    assert observation.value == "stopped"


def test_ignores_unknown_topic():
    adapter, _ = _build_adapter()

    observation = adapter.ingest_message(
        topic="dnake/curtain/主卧窗帘/state",
        raw_payload="OPEN",
    )

    assert observation is None


def test_rejects_unknown_curtain_state():
    adapter, _ = _build_adapter()

    try:
        adapter.ingest_message(
            topic="dnake/curtain/客厅窗帘/state",
            raw_payload="MOVING",
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "unsupported dnake curtain state: MOVING"
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )



def _build_light_adapter():
    device = DeviceDefinition(
        device_id="living.light_strip_1",
        name="客厅灯带",
        location_id="living",
        adapter_id="dnake_mqtt",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id=(
                    "dnake/light/客厅灯带/state"
                ),
                value_type="bool",
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
        DnakeMqttDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_maps_light_on_to_canonical_true():
    adapter, store = _build_light_adapter()

    observation = adapter.ingest_message(
        topic="dnake/light/客厅灯带/state",
        raw_payload="ON",
    )

    assert observation.value is True
    assert (
        store.get(
            "living.light_strip_1",
            "power",
        ).value
        is True
    )


def test_maps_light_off_to_canonical_false():
    adapter, store = _build_light_adapter()

    observation = adapter.ingest_message(
        topic="dnake/light/客厅灯带/state",
        raw_payload="OFF",
    )

    assert observation.value is False
    assert (
        store.get(
            "living.light_strip_1",
            "power",
        ).value
        is False
    )


def _build_air_conditioner_adapter():
    topic = "dnake/air/客厅空调/state"

    device = DeviceDefinition(
        device_id="air_conditioner_001",
        name="客厅空调",
        location_id="living",
        adapter_id="dnake_mqtt",
        parameters={
            "operating_state": (
                DeviceParameterDefinition(
                    parameter="operating_state",
                    source_id=(
                        topic
                        + "#operating_state"
                    ),
                    value_type="string",
                )
            ),
            "target_temperature": (
                DeviceParameterDefinition(
                    parameter="target_temperature",
                    source_id=(
                        topic
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
                        topic
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
                        topic
                        + "#fan_mode"
                    ),
                    value_type="string",
                )
            ),
        },
        adapter_config={
            "state_topic": topic,
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
        DnakeMqttDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        ),
        store,
    )


def test_air_conditioner_state_message_fans_out_canonical_parameters():
    import json

    adapter, store = (
        _build_air_conditioner_adapter()
    )

    observations = adapter.ingest_message(
        topic="dnake/air/客厅空调/state",
        raw_payload=json.dumps(
            {
                "power": "ON",
                "power_raw": 1,
                "mode": "COOL",
                "mode_raw": 1,
                "temp_set": 23,
                "temp_room": 28,
                "fan": "LOW",
                "fan_raw": 1,
                "swing": "OFF",
                "swing_raw": 0,
            }
        ),
    )

    assert len(observations) == 4

    assert (
        store.get(
            "air_conditioner_001",
            "operating_state",
        ).value
        == "cool"
    )

    assert (
        store.get(
            "air_conditioner_001",
            "target_temperature",
        ).value
        == 23.0
    )

    assert (
        store.get(
            "air_conditioner_001",
            "current_temperature",
        ).value
        == 28.0
    )

    assert (
        store.get(
            "air_conditioner_001",
            "fan_mode",
        ).value
        == "low"
    )


def test_air_conditioner_power_off_overrides_reported_mode():
    import json

    adapter, store = (
        _build_air_conditioner_adapter()
    )

    adapter.ingest_message(
        topic="dnake/air/客厅空调/state",
        raw_payload=json.dumps(
            {
                "power": "OFF",
                "mode": "COOL",
                "temp_set": 23,
                "temp_room": 28,
                "fan": "LOW",
            }
        ),
    )

    assert (
        store.get(
            "air_conditioner_001",
            "operating_state",
        ).value
        == "off"
    )


def test_air_conditioner_does_not_publish_vendor_raw_fields():
    import json

    adapter, store = (
        _build_air_conditioner_adapter()
    )

    adapter.ingest_message(
        topic="dnake/air/客厅空调/state",
        raw_payload=json.dumps(
            {
                "power": "ON",
                "power_raw": 1,
                "mode": "HEAT",
                "mode_raw": 2,
                "temp_set": 24,
                "temp_room": 27,
                "fan": "MEDIUM",
                "fan_raw": 2,
                "swing": "ON",
                "swing_raw": 1,
            }
        ),
    )

    assert {
        entry.parameter
        for entry in store.for_device(
            "air_conditioner_001"
        )
    } == {
        "operating_state",
        "target_temperature",
        "current_temperature",
        "fan_mode",
    }


def test_air_conditioner_unknown_fan_is_unavailable():
    import json

    adapter, store = (
        _build_air_conditioner_adapter()
    )

    observations = adapter.ingest_message(
        topic="dnake/air/客厅空调/state",
        raw_payload=json.dumps(
            {
                "power": "OFF",
                "power_raw": 0,
                "mode": "COOL",
                "mode_raw": 2,
                "temp_set": 23,
                "temp_room": 28,
                "fan": "UNKNOWN",
                "fan_raw": 0,
                "swing": "OFF",
                "swing_raw": 0,
            }
        ),
    )

    fan_entry = store.get(
        "air_conditioner_001",
        "fan_mode",
    )

    assert fan_entry is not None
    assert fan_entry.available is False
    assert fan_entry.value is None

    fan_observation = next(
        observation
        for observation in observations
        if observation.parameter
        == "fan_mode"
    )

    assert (
        fan_observation.quality
        == "unavailable"
    )
    assert fan_observation.value is None

    assert (
        store.get(
            "air_conditioner_001",
            "operating_state",
        ).value
        == "off"
    )

    assert (
        store.get(
            "air_conditioner_001",
            "target_temperature",
        ).value
        == 23.0
    )

    assert (
        store.get(
            "air_conditioner_001",
            "current_temperature",
        ).value
        == 28.0
    )


def test_restores_retained_light_state_without_creating_observation():
    device = DeviceDefinition(
        device_id="living.light_strip_1",
        name="客厅灯带",
        location_id="living",
        adapter_id="dnake_mqtt",
        parameters={
            "power": DeviceParameterDefinition(
                parameter="power",
                source_id=(
                    "dnake/light/客厅灯带/state"
                ),
                value_type="bool",
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

    class FailingBridge:
        def convert(self, *args, **kwargs):
            raise AssertionError(
                "retained restore must not "
                "create an Observation"
            )

    ingestion._bridge = FailingBridge()

    adapter = DnakeMqttDeviceDataAdapter(
        registry=registry,
        ingestion=ingestion,
    )

    entry = adapter.restore_message(
        topic="dnake/light/客厅灯带/state",
        raw_payload="OFF",
    )

    assert entry.value is False
    assert entry.updated_at == ""

    stored = store.get(
        "living.light_strip_1",
        "power",
    )

    assert stored.value is False
    assert stored.updated_at == ""

def test_fresh_light_state_replaces_restored_state_and_creates_observation():
    adapter, store = _build_light_adapter()

    restored = adapter.restore_message(
        topic="dnake/light/客厅灯带/state",
        raw_payload="OFF",
    )

    assert restored.value is False
    assert restored.updated_at == ""

    observation = adapter.ingest_message(
        topic="dnake/light/客厅灯带/state",
        raw_payload="ON",
    )

    stored = store.get(
        "living.light_strip_1",
        "power",
    )

    assert stored.value is True
    assert stored.updated_at
    assert observation.value is True
    assert (
        observation.observed_at
        == stored.updated_at
    )

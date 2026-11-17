import pytest

from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceParameterStore,
    DeviceParameterStoreError,
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
                },
            )
        ]
    )


def test_store_updates_registered_device_parameter():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    entry = store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49.0,
        available=True,
    )

    assert entry.device_id == (
        "living.presence_sensor_1"
    )
    assert entry.location_id == "living"
    assert entry.parameter == "illuminance"
    assert entry.value == 49.0
    assert entry.unit == "lux"
    assert entry.available is True
    assert entry.updated_at


def test_store_get_returns_latest_parameter_value():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=12.0,
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49.0,
    )

    entry = store.get(
        "living.presence_sensor_1",
        "illuminance",
    )

    assert entry is not None
    assert entry.value == 49.0


def test_store_keeps_multiple_parameters_for_same_device():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="presence",
        value=True,
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49.0,
    )

    snapshot = store.snapshot()

    assert len(snapshot) == 2

    by_parameter = {
        item.parameter: item
        for item in snapshot
    }

    assert by_parameter["presence"].value is True
    assert (
        by_parameter["illuminance"].value
        == 49.0
    )


def test_store_rejects_unknown_device():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    with pytest.raises(
        DeviceParameterStoreError
    ):
        store.update(
            device_id="unknown.device",
            parameter="illuminance",
            value=49,
        )


def test_store_rejects_unknown_parameter():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    with pytest.raises(
        DeviceParameterStoreError
    ):
        store.update(
            device_id="living.presence_sensor_1",
            parameter="temperature",
            value=25,
        )


def test_store_uses_parameter_definition_unit():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    entry = store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49,
    )

    assert entry.unit == "lux"


def test_store_snapshot_returns_copies():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49,
    )

    first = store.snapshot()
    second = store.snapshot()

    assert first == second
    assert first is not second


def test_store_updates_from_resolved_source():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    entry = store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
        available=True,
    )

    assert entry.device_id == (
        "living.presence_sensor_1"
    )
    assert entry.location_id == "living"
    assert entry.parameter == "illuminance"
    assert entry.value == 49.0
    assert entry.unit == "lux"


def test_store_rejects_unknown_source():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    with pytest.raises(
        DeviceParameterStoreError
    ):
        store.update_source(
            adapter_id="home_assistant",
            source_id="sensor.unknown",
            value=49.0,
        )


def test_source_update_and_direct_update_share_same_slot():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=12.0,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    entry = store.get(
        "living.presence_sensor_1",
        "illuminance",
    )

    assert entry is not None
    assert entry.value == 49.0


def test_store_can_read_all_parameters_for_device():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="presence",
        value=True,
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49.0,
    )

    entries = store.for_device(
        "living.presence_sensor_1"
    )

    assert {
        entry.parameter
        for entry in entries
    } == {
        "presence",
        "illuminance",
    }


def test_store_can_read_all_parameters_for_location():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="presence",
        value=True,
    )

    store.update(
        device_id="living.presence_sensor_1",
        parameter="illuminance",
        value=49.0,
    )

    entries = store.for_location(
        "living"
    )

    assert len(entries) == 2

    assert {
        entry.device_id
        for entry in entries
    } == {
        "living.presence_sensor_1",
    }


def test_store_location_query_does_not_mix_locations():
    registry = DeviceRegistry(
        devices=[
            DeviceDefinition(
                device_id="living.sensor_1",
                name="客厅传感器",
                location_id="living",
                adapter_id="home_assistant",
                parameters={
                    "illuminance": (
                        DeviceParameterDefinition(
                            parameter="illuminance",
                            source_id="sensor.living_lux",
                            value_type="float",
                            unit="lux",
                        )
                    ),
                },
            ),
            DeviceDefinition(
                device_id="corridor.sensor_1",
                name="过廊传感器",
                location_id="corridor",
                adapter_id="home_assistant",
                parameters={
                    "illuminance": (
                        DeviceParameterDefinition(
                            parameter="illuminance",
                            source_id="sensor.corridor_lux",
                            value_type="float",
                            unit="lux",
                        )
                    ),
                },
            ),
        ]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="living.sensor_1",
        parameter="illuminance",
        value=50.0,
    )

    store.update(
        device_id="corridor.sensor_1",
        parameter="illuminance",
        value=20.0,
    )

    entries = store.for_location(
        "living"
    )

    assert len(entries) == 1
    assert entries[0].device_id == "living.sensor_1"
    assert entries[0].value == 50.0


def test_store_restores_parameter_without_fabricating_updated_at():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    entry = store.restore(
        device_id="living.presence_sensor_1",
        parameter="presence",
        value=True,
        available=True,
    )

    assert entry.device_id == (
        "living.presence_sensor_1"
    )
    assert entry.parameter == "presence"
    assert entry.value is True
    assert entry.available is True
    assert entry.updated_at == ""

    stored = store.get(
        "living.presence_sensor_1",
        "presence",
    )

    assert stored == entry


def test_store_restores_source_without_fabricating_updated_at():
    store = DeviceParameterStore(
        registry=make_registry()
    )

    entry = store.restore_source(
        adapter_id="home_assistant",
        source_id=(
            "binary_sensor."
            "living_presence"
        ),
        value=False,
        available=True,
    )

    assert entry.value is False
    assert entry.updated_at == ""

    stored = store.get(
        "living.presence_sensor_1",
        "presence",
    )

    assert stored == entry


def test_ingestion_restore_does_not_create_observation():
    from src.smartscreen_platform.device_data import (
        DeviceDataIngestionService,
    )

    registry = make_registry()
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
                "restored state must not "
                "be converted into an Observation"
            )

    ingestion._bridge = FailingBridge()

    entry = ingestion.restore(
        adapter_id="home_assistant",
        source_id=(
            "binary_sensor."
            "living_presence"
        ),
        value=True,
        available=True,
    )

    assert entry.value is True
    assert entry.updated_at == ""


def test_store_restore_does_not_call_clock():
    def fail_clock():
        raise AssertionError(
            "restore must not fabricate "
            "an observation timestamp"
        )

    store = DeviceParameterStore(
        registry=make_registry(),
        clock=fail_clock,
    )

    entry = store.restore(
        device_id="living.presence_sensor_1",
        parameter="presence",
        value=True,
        available=True,
    )

    assert entry.value is True
    assert entry.updated_at == ""

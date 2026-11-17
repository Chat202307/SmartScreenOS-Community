import pytest

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
                },
            )
        ]
    )


def test_ingestion_updates_store_and_returns_observation():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    service = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    observation = service.ingest(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
        available=True,
    )

    entry = store.get(
        "living.presence_sensor_1",
        "illuminance",
    )

    assert entry is not None
    assert entry.value == 49.0

    assert observation.parameter == "illuminance"
    assert observation.value == 49.0
    assert observation.unit == "lux"
    assert observation.location_id == "living"


def test_ingestion_preserves_source_traceability():
    registry = make_registry()

    service = DeviceDataIngestionService(
        registry=registry,
        store=DeviceParameterStore(
            registry=registry
        ),
    )

    observation = service.ingest(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    assert (
        observation.provenance["device_id"]
        == "living.presence_sensor_1"
    )

    assert (
        observation.provenance["source_id"]
        == "sensor.living_illuminance"
    )


def test_ingestion_rejects_unknown_source():
    registry = make_registry()

    service = DeviceDataIngestionService(
        registry=registry,
        store=DeviceParameterStore(
            registry=registry
        ),
    )

    with pytest.raises(ValueError):
        service.ingest(
            adapter_id="home_assistant",
            source_id="sensor.unknown",
            value=49.0,
        )


def test_unavailable_ingestion_marks_observation_unavailable():
    registry = make_registry()

    service = DeviceDataIngestionService(
        registry=registry,
        store=DeviceParameterStore(
            registry=registry
        ),
    )

    observation = service.ingest(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
        available=False,
    )

    assert observation.quality == "unavailable"

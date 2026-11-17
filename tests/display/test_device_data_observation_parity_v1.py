from pathlib import Path

import pytest

from src.smartscreen_display.device_data_config import (
    load_device_definitions,
)
from src.smartscreen_display.home_assistant_observations import (
    HomeAssistantObservationAdapter,
)
from src.smartscreen_platform.device_data import (
    DeviceDataIngestionService,
    DeviceParameterStore,
    DeviceRegistry,
)


PROJECT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DEVICE_DATA_CONFIG = (
    PROJECT
    / "config"
    / "device_data.json"
)

LEGACY_PARITY_ENTITIES = [
    {
        "entity_id":
            "binary_sensor.demo_entity_010",
        "parameter": "presence",
        "location_id": "open_public_area",
        "value_type": "bool",
    },
    {
        "entity_id":
            "sensor.demo_entity_051",
        "parameter": "illuminance",
        "location_id": "kitchen",
        "value_type": "float",
        "unit": "lux",
    },
    {
        "entity_id":
            "binary_sensor.demo_entity_012",
        "parameter": "presence",
        "location_id": "guest_bath",
        "value_type": "bool",
    },
    {
        "entity_id":
            "sensor.demo_entity_053",
        "parameter": "illuminance",
        "location_id": "guest_bath",
        "value_type": "float",
        "unit": "lux",
    },
    {
        "entity_id":
            "binary_sensor.demo_entity_011",
        "parameter": "presence",
        "location_id": "master_bath",
        "value_type": "bool",
    },
    {
        "entity_id":
            "sensor.demo_entity_052",
        "parameter": "illuminance",
        "location_id": "master_bath",
        "value_type": "float",
        "unit": "lux",
    },
    {
        "entity_id":
            "sensor.demo_entity_037",
        "parameter": "motion_idle_seconds",
        "location_id": "corridor",
        "value_type": "int",
        "unit": "s",
    },
    {
        "entity_id":
            "sensor.demo_entity_036",
        "parameter": "illuminance",
        "location_id": "corridor",
        "value_type": "float",
        "unit": "lux",
    },
]


@pytest.fixture
def old_adapter():
    return HomeAssistantObservationAdapter(
        entities=LEGACY_PARITY_ENTITIES
    )


@pytest.fixture
def new_ingestion():
    registry = DeviceRegistry(
        devices=load_device_definitions(
            DEVICE_DATA_CONFIG
        )
    )

    store = DeviceParameterStore(
        registry=registry
    )

    return DeviceDataIngestionService(
        registry=registry,
        store=store,
    )


CASES = [
    (
        "binary_sensor.demo_entity_010",
        "on",
    ),
    (
        "sensor.demo_entity_051",
        "49",
    ),
    (
        "binary_sensor.demo_entity_012",
        "off",
    ),
    (
        "sensor.demo_entity_053",
        "2",
    ),
    (
        "binary_sensor.demo_entity_011",
        "on",
    ),
    (
        "sensor.demo_entity_052",
        "42",
    ),
    (
        "sensor.demo_entity_037",
        "300",
    ),
    (
        "sensor.demo_entity_036",
        "45",
    ),
]


def convert_new(
    service,
    *,
    entity_id,
    raw_state,
):
    registry = service._registry

    binding = registry.resolve_source(
        adapter_id="home_assistant",
        source_id=entity_id,
    )

    assert binding is not None

    value_type = binding.value_type

    if value_type == "float":
        value = float(raw_state)
    elif value_type == "int":
        value = int(raw_state)
    elif value_type == "bool":
        if raw_state in {
            True,
            "on",
            "true",
            "1",
            1,
        }:
            value = True
        elif raw_state in {
            False,
            "off",
            "false",
            "0",
            0,
        }:
            value = False
        else:
            raise ValueError(
                "invalid boolean value"
            )
    else:
        value = str(raw_state)

    return service.ingest(
        adapter_id="home_assistant",
        source_id=entity_id,
        value=value,
        available=True,
    )





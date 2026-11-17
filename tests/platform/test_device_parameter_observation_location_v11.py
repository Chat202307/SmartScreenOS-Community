from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceParameterDefinition,
    DeviceRegistry,
)


def make_device():
    return DeviceDefinition(
        device_id="kitchen.sensor_1",
        name="厨房人体",
        location_id="kitchen",
        adapter_id="home_assistant",
        parameters={
            "presence": DeviceParameterDefinition(
                parameter="presence",
                source_id="binary_sensor.kitchen_presence",
                value_type="bool",
                observation_location_id=(
                    "open_public_area"
                ),
            ),
            "illuminance": DeviceParameterDefinition(
                parameter="illuminance",
                source_id="sensor.kitchen_lux",
                value_type="float",
                unit="lux",
            ),
        },
    )


def test_parameter_can_override_device_location():
    registry = DeviceRegistry(
        devices=[make_device()]
    )

    binding = registry.resolve_parameter(
        device_id="kitchen.sensor_1",
        parameter="presence",
    )

    assert binding.location_id == (
        "open_public_area"
    )


def test_parameter_without_override_uses_device_location():
    registry = DeviceRegistry(
        devices=[make_device()]
    )

    binding = registry.resolve_parameter(
        device_id="kitchen.sensor_1",
        parameter="illuminance",
    )

    assert binding.location_id == "kitchen"


def test_device_physical_location_remains_independent():
    registry = DeviceRegistry(
        devices=[make_device()]
    )

    device = registry.get(
        "kitchen.sensor_1"
    )

    assert device.location_id == "kitchen"


def test_ingested_parameter_uses_observation_location_override():
    from src.smartscreen_platform.device_data import (
        DeviceDataIngestionService,
        DeviceParameterStore,
    )

    registry = DeviceRegistry(
        devices=[make_device()]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    service = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    observation = service.ingest(
        adapter_id="home_assistant",
        source_id="binary_sensor.kitchen_presence",
        value=True,
    )

    assert (
        observation.location_id
        == "open_public_area"
    )


def test_ingested_parameter_without_override_uses_device_location():
    from src.smartscreen_platform.device_data import (
        DeviceDataIngestionService,
        DeviceParameterStore,
    )

    registry = DeviceRegistry(
        devices=[make_device()]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    service = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    observation = service.ingest(
        adapter_id="home_assistant",
        source_id="sensor.kitchen_lux",
        value=18.0,
    )

    assert (
        observation.location_id
        == "kitchen"
    )


def test_store_location_queries_follow_parameter_observation_locations():
    from src.smartscreen_platform.device_data import (
        DeviceParameterStore,
    )

    registry = DeviceRegistry(
        devices=[make_device()]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    store.update(
        device_id="kitchen.sensor_1",
        parameter="presence",
        value=True,
    )

    store.update(
        device_id="kitchen.sensor_1",
        parameter="illuminance",
        value=18.0,
    )

    open_area_entries = store.for_location(
        "open_public_area"
    )

    kitchen_entries = store.for_location(
        "kitchen"
    )

    assert [
        item.parameter
        for item in open_area_entries
    ] == [
        "presence"
    ]

    assert [
        item.parameter
        for item in kitchen_entries
    ] == [
        "illuminance"
    ]

    assert (
        open_area_entries[0].device_id
        == "kitchen.sensor_1"
    )

    assert (
        kitchen_entries[0].device_id
        == "kitchen.sensor_1"
    )

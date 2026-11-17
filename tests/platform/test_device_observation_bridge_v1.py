from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceObservationBridge,
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


def test_bridge_builds_observation_from_device_parameter():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    entry = store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    bridge = DeviceObservationBridge(
        registry=registry
    )

    observation = bridge.convert(
        entry,
        source_id="sensor.living_illuminance",
    )

    assert observation.parameter == "illuminance"
    assert observation.value == 49.0
    assert observation.unit == "lux"
    assert observation.location_id == "living"


def test_bridge_preserves_device_traceability_in_provenance():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    entry = store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observation = DeviceObservationBridge(
        registry=registry
    ).convert(
        entry,
        source_id="sensor.living_illuminance",
    )

    assert observation.provenance == {
        "provider": "home_assistant",
        "adapter_id": "home_assistant",
        "device_id": "living.presence_sensor_1",
        "source_id": "sensor.living_illuminance",
    }


def test_bridge_does_not_add_device_id_to_observation_contract():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    entry = store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observation = DeviceObservationBridge(
        registry=registry
    ).convert(
        entry,
        source_id="sensor.living_illuminance",
    )

    payload = observation.to_dict()

    assert "device_id" not in payload
    assert (
        payload["provenance"]["device_id"]
        == "living.presence_sensor_1"
    )


def test_bridge_uses_parameter_availability_as_quality():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    entry = store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
        available=False,
    )

    observation = DeviceObservationBridge(
        registry=registry
    ).convert(
        entry,
        source_id="sensor.living_illuminance",
    )

    assert observation.quality == "unavailable"


def test_bridge_converts_store_snapshot_without_external_source_ids():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="binary_sensor.living_presence",
        value=True,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    bridge = DeviceObservationBridge(
        registry=registry
    )

    observations = bridge.snapshot(
        store
    )

    by_parameter = {
        observation.parameter: observation
        for observation in observations
    }

    assert set(by_parameter) == {
        "presence",
        "illuminance",
    }

    assert (
        by_parameter["presence"].value
        is True
    )

    assert (
        by_parameter["illuminance"].value
        == 49.0
    )

    assert (
        by_parameter["illuminance"].location_id
        == "living"
    )

    assert (
        by_parameter["illuminance"]
        .provenance["device_id"]
        == "living.presence_sensor_1"
    )

    assert (
        by_parameter["illuminance"]
        .provenance["source_id"]
        == "sensor.living_illuminance"
    )


def test_bridge_snapshot_preserves_unavailable_quality():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
        available=False,
    )

    observations = (
        DeviceObservationBridge(
            registry=registry
        ).snapshot(
            store
        )
    )

    assert len(observations) == 1
    assert (
        observations[0].quality
        == "unavailable"
    )


def test_bridge_snapshot_does_not_expose_vendor_identity_at_observation_top_level():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observation = (
        DeviceObservationBridge(
            registry=registry
        ).snapshot(
            store
        )[0]
    )

    payload = observation.to_dict()

    assert "device_id" not in payload
    assert "source_id" not in payload

    assert (
        payload["provenance"][
            "device_id"
        ]
        == "living.presence_sensor_1"
    )


def test_bridge_can_convert_observations_for_device():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="binary_sensor.living_presence",
        value=True,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observations = (
        DeviceObservationBridge(
            registry=registry
        ).for_device(
            store,
            "living.presence_sensor_1",
        )
    )

    assert {
        observation.parameter
        for observation in observations
    } == {
        "presence",
        "illuminance",
    }

    assert {
        observation.location_id
        for observation in observations
    } == {
        "living",
    }


def test_bridge_can_convert_observations_for_location():
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

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_lux",
        value=50.0,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.corridor_lux",
        value=20.0,
    )

    observations = (
        DeviceObservationBridge(
            registry=registry
        ).for_location(
            store,
            "living",
        )
    )

    assert len(observations) == 1
    assert observations[0].parameter == "illuminance"
    assert observations[0].value == 50.0
    assert observations[0].location_id == "living"


def test_bridge_local_queries_preserve_source_provenance():
    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observation = (
        DeviceObservationBridge(
            registry=registry
        ).for_device(
            store,
            "living.presence_sensor_1",
        )[0]
    )

    assert (
        observation.provenance["source_id"]
        == "sensor.living_illuminance"
    )
    assert (
        observation.provenance["device_id"]
        == "living.presence_sensor_1"
    )


def test_bridge_preserves_device_parameter_updated_at_as_observed_at():
    from datetime import datetime, timezone

    fixed_time = datetime(
        2026,
        8,
        16,
        8,
        30,
        0,
        tzinfo=timezone.utc,
    )

    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry,
        clock=lambda: fixed_time,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observation = (
        DeviceObservationBridge(
            registry=registry
        ).for_device(
            store,
            "living.presence_sensor_1",
        )[0]
    )

    assert (
        observation.observed_at
        == fixed_time.isoformat()
    )


def test_device_data_observations_respect_existing_accumulator_freshness():
    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )

    class FakeClock:
        def __init__(self):
            self.current = datetime(
                2026,
                8,
                16,
                8,
                30,
                0,
                tzinfo=timezone.utc,
            )

        def now(self):
            return self.current

        def advance(self, seconds):
            self.current += timedelta(
                seconds=seconds
            )

    clock = FakeClock()

    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry,
        clock=clock.now,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="binary_sensor.living_presence",
        value=True,
    )

    bridge = DeviceObservationBridge(
        registry=registry
    )

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    accumulator.update(
        bridge.for_location(
            store,
            "living",
        )
    )

    clock.advance(61)

    assert (
        accumulator.for_location(
            "living"
        )
        == []
    )


def test_device_data_observations_drive_existing_semantic_pipeline():
    from src.smartscreen_platform.capabilities.lighting import (
        LightingCapability,
    )
    from src.smartscreen_platform.capabilities.occupancy import (
        OccupancyCapability,
    )
    from src.smartscreen_platform.household_state import (
        HouseholdStateEngine,
    )
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
        PresenceInterpreter,
    )
    from src.smartscreen_platform.state_pipeline import (
        PlatformStatePipeline,
    )

    registry = make_registry()

    store = DeviceParameterStore(
        registry=registry
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="binary_sensor.living_presence",
        value=True,
    )

    store.update_source(
        adapter_id="home_assistant",
        source_id="sensor.living_illuminance",
        value=49.0,
    )

    observations = (
        DeviceObservationBridge(
            registry=registry
        ).for_location(
            store,
            "living",
        )
    )

    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            PresenceInterpreter(),
            IlluminanceInterpreter(),
        ],
        capabilities=[
            OccupancyCapability(),
            LightingCapability(),
        ],
    )

    pipeline.process(
        observations
    )

    occupancy = household_state.get(
        "occupancy",
        location_id="living",
    )

    lighting = household_state.get(
        "lighting",
        location_id="living",
    )

    assert occupancy is not None
    assert occupancy.value == {
        "state": "occupied",
        "count": None,
    }

    assert lighting is not None
    assert lighting.value == {
        "state": "dim",
    }

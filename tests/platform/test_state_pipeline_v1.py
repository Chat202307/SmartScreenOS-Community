from src.smartscreen_platform.capabilities.comfort import (
    ComfortCapability,
)
from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)
from src.smartscreen_platform.interpretation import (
    ThermalInterpreter,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)


def test_pipeline_writes_comfort_state_to_household_state():
    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            ThermalInterpreter(),
        ],
        capabilities=[
            ComfortCapability(),
        ],
    )

    temperature = Observation.create(
        "temperature",
        29,
        unit="degC",
        confidence=0.98,
        location_id="living",
    )

    humidity = Observation.create(
        "humidity",
        75,
        unit="percent",
        confidence=0.90,
        location_id="living",
    )

    pipeline.process([
        temperature,
        humidity,
    ])

    entry = household_state.get(
        "comfort",
        location_id="living",
    )

    assert entry is not None
    assert entry.target == "comfort"
    assert entry.location_id == "living"
    assert (
        entry.value["level"]
        == "slightly_uncomfortable"
    )

    assert temperature.observation_id in entry.evidence_refs
    assert humidity.observation_id in entry.evidence_refs


def test_pipeline_requires_sufficient_evidence_for_comfort():
    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            ThermalInterpreter(),
        ],
        capabilities=[
            ComfortCapability(),
        ],
    )

    entries = pipeline.process([
        Observation.create(
            "temperature",
            24,
            unit="degC",
            location_id="living",
        ),
    ])

    assert entries == []

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is None
    )

def test_pipeline_handles_missing_required_observations():
    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            ThermalInterpreter(),
        ],
        capabilities=[
            ComfortCapability(),
        ],
    )

    entries = pipeline.process([])

    assert entries == []
    assert household_state.snapshot() == []


def test_state_pipeline_keeps_observations_isolated_by_location():
    from src.smartscreen_platform.capabilities.comfort import (
        ComfortCapability,
    )
    from src.smartscreen_platform.contracts import Observation
    from src.smartscreen_platform.household_state import (
        HouseholdStateEngine,
    )
    from src.smartscreen_platform.interpretation import (
        ThermalInterpreter,
    )

    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[ThermalInterpreter()],
        capabilities=[ComfortCapability()],
    )

    observations = [
        Observation.create(
            "temperature",
            31,
            unit="degC",
            location_id="living",
        ),
        Observation.create(
            "humidity",
            75,
            unit="percent",
            location_id="living",
        ),
        Observation.create(
            "temperature",
            23,
            unit="degC",
            location_id="bedroom",
        ),
        Observation.create(
            "humidity",
            45,
            unit="percent",
            location_id="bedroom",
        ),
    ]

    entries = pipeline.process(observations)

    assert len(entries) == 2

    by_location = {
        entry.location_id: entry
        for entry in entries
    }

    assert set(by_location) == {
        "living",
        "bedroom",
    }

    assert (
        by_location["living"].value["dimensions"]["thermal"]
        == "hot"
    )

    assert (
        by_location["bedroom"].value["dimensions"]["thermal"]
        == "comfortable"
    )


def test_state_pipeline_keeps_evidence_isolated_by_location():
    from src.smartscreen_platform.capabilities.comfort import (
        ComfortCapability,
    )
    from src.smartscreen_platform.contracts import Observation
    from src.smartscreen_platform.household_state import (
        HouseholdStateEngine,
    )
    from src.smartscreen_platform.interpretation import (
        ThermalInterpreter,
    )

    living_temperature = Observation.create(
        "temperature",
        31,
        unit="degC",
        location_id="living",
    )
    living_humidity = Observation.create(
        "humidity",
        75,
        unit="percent",
        location_id="living",
    )
    bedroom_temperature = Observation.create(
        "temperature",
        23,
        unit="degC",
        location_id="bedroom",
    )
    bedroom_humidity = Observation.create(
        "humidity",
        45,
        unit="percent",
        location_id="bedroom",
    )

    pipeline = PlatformStatePipeline(
        household_state=HouseholdStateEngine(),
        interpreters=[ThermalInterpreter()],
        capabilities=[ComfortCapability()],
    )

    entries = pipeline.process(
        [
            living_temperature,
            living_humidity,
            bedroom_temperature,
            bedroom_humidity,
        ]
    )

    by_location = {
        entry.location_id: entry
        for entry in entries
    }

    assert set(
        by_location["living"].evidence_refs
    ) == {
        living_temperature.observation_id,
        living_humidity.observation_id,
    }

    assert set(
        by_location["bedroom"].evidence_refs
    ) == {
        bedroom_temperature.observation_id,
        bedroom_humidity.observation_id,
    }

    assert (
        bedroom_temperature.observation_id
        not in by_location["living"].evidence_refs
    )
    assert (
        bedroom_humidity.observation_id
        not in by_location["living"].evidence_refs
    )

    assert (
        living_temperature.observation_id
        not in by_location["bedroom"].evidence_refs
    )
    assert (
        living_humidity.observation_id
        not in by_location["bedroom"].evidence_refs
    )

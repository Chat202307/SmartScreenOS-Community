from src.smartscreen_platform.capabilities.occupancy import (
    OccupancyCapability,
)
from src.smartscreen_platform.contracts import (
    Observation,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)
from src.smartscreen_platform.interpretation import (
    PresenceInterpreter,
)


def interpret_presence(
    value,
    *,
    count=None,
    confidence=1.0,
    location_id="living",
):
    observations = [
        Observation.create(
            "presence",
            value,
            confidence=confidence,
            location_id=location_id,
        )
    ]

    if count is not None:
        observations.append(
            Observation.create(
                "occupancy_count",
                count,
                confidence=confidence,
                location_id=location_id,
            )
        )

    interpretations = (
        PresenceInterpreter().interpret(
            observations
        )
    )

    return observations, interpretations


def test_occupancy_capability_creates_occupied_state():
    observations, interpretations = (
        interpret_presence(True)
    )

    patches = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )

    assert len(patches) == 1

    patch = patches[0]

    assert patch.capability == "occupancy"
    assert patch.target == "occupancy"
    assert patch.location_id == "living"

    assert patch.value == {
        "state": "occupied",
        "count": None,
    }

    assert patch.ttl_seconds == 60


def test_occupancy_capability_creates_unoccupied_state():
    observations, interpretations = (
        interpret_presence(False)
    )

    patch = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    assert patch.value == {
        "state": "unoccupied",
        "count": 0,
    }


def test_occupancy_capability_preserves_count():
    observations, interpretations = (
        interpret_presence(
            True,
            count=3,
        )
    )

    patch = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    assert patch.value == {
        "state": "occupied",
        "count": 3,
    }


def test_occupancy_capability_preserves_location():
    observations, interpretations = (
        interpret_presence(
            True,
            location_id="bedroom",
        )
    )

    patch = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    assert patch.location_id == "bedroom"


def test_occupancy_capability_preserves_confidence():
    observations, interpretations = (
        interpret_presence(
            True,
            confidence=0.82,
        )
    )

    patch = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    assert patch.confidence == 0.82


def test_occupancy_capability_uses_interpretation_evidence():
    observations, interpretations = (
        interpret_presence(True)
    )

    interpretation = interpretations[0]

    patch = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    assert patch.evidence_refs == (
        interpretation.evidence_refs
    )


def test_occupancy_capability_ignores_unrelated_interpretations():
    observations = [
        Observation.create(
            "temperature",
            25,
            unit="degC",
            location_id="living",
        )
    ]

    assert (
        OccupancyCapability().evaluate(
            [],
            observations=observations,
        )
        == []
    )


def test_occupancy_capability_applies_to_household_state():
    observations, interpretations = (
        interpret_presence(True)
    )

    patch = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    entry = HouseholdStateEngine().apply(
        patch
    )

    assert entry.target == "occupancy"
    assert entry.location_id == "living"
    assert entry.source_capability == "occupancy"

    assert entry.value == {
        "state": "occupied",
        "count": None,
    }

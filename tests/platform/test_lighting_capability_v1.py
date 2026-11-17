from src.smartscreen_platform.contracts import (
    Interpretation,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)


def make_lighting(
    value,
    *,
    location_id="corridor",
    confidence=0.95,
    evidence_refs=None,
):
    return Interpretation.create(
        interpretation_type="lighting_state",
        name="lighting_state",
        value=value,
        confidence=confidence,
        location_id=location_id,
        evidence_refs=(
            evidence_refs
            or ["observation:illuminance-1"]
        ),
        expires_in_seconds=300,
        metadata={
            "dim_below_lux": 80.0,
            "bright_above_lux": 1200.0,
        },
    )


def test_lighting_capability_projects_dim_state():
    from src.smartscreen_platform.capabilities.lighting import (
        LightingCapability,
    )

    lighting = make_lighting(
        "dim",
        location_id="corridor",
    )

    patches = LightingCapability().evaluate(
        [lighting]
    )

    assert len(patches) == 1

    patch = patches[0]

    assert patch.capability == "lighting"
    assert patch.target == "lighting"
    assert patch.value == {
        "state": "dim",
    }
    assert patch.location_id == "corridor"
    assert patch.confidence == 0.95
    assert patch.ttl_seconds == 300
    assert patch.evidence_refs == [
        "observation:illuminance-1"
    ]


def test_lighting_capability_projects_comfortable_state():
    from src.smartscreen_platform.capabilities.lighting import (
        LightingCapability,
    )

    patch = LightingCapability().evaluate(
        [
            make_lighting(
                "comfortable",
                location_id="living",
            )
        ]
    )[0]

    assert patch.value == {
        "state": "comfortable",
    }
    assert patch.location_id == "living"


def test_lighting_capability_projects_bright_state():
    from src.smartscreen_platform.capabilities.lighting import (
        LightingCapability,
    )

    patch = LightingCapability().evaluate(
        [
            make_lighting(
                "bright",
                location_id="living",
            )
        ]
    )[0]

    assert patch.value == {
        "state": "bright",
    }


def test_lighting_capability_ignores_missing_lighting_state():
    from src.smartscreen_platform.capabilities.lighting import (
        LightingCapability,
    )

    thermal = Interpretation.create(
        interpretation_type="thermal_state",
        name="thermal_state",
        value="comfortable",
        confidence=0.9,
        location_id="corridor",
    )

    assert (
        LightingCapability().evaluate(
            [thermal]
        )
        == []
    )


def test_lighting_capability_projects_to_household_state():
    from src.smartscreen_platform.capabilities.lighting import (
        LightingCapability,
    )

    patch = LightingCapability().evaluate(
        [
            make_lighting(
                "dim",
                location_id="corridor",
            )
        ]
    )[0]

    engine = HouseholdStateEngine()

    entry = engine.apply(
        patch
    )

    assert entry.target == "lighting"
    assert entry.location_id == "corridor"
    assert entry.value == {
        "state": "dim",
    }
    assert entry.evidence_refs == [
        "observation:illuminance-1"
    ]

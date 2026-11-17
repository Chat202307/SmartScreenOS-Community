from dataclasses import replace
from datetime import datetime, timedelta, timezone

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
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)


class FakeClock:
    def __init__(self):
        self.current = datetime(
            2026,
            8,
            12,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def now(self):
        return self.current

    def advance(self, seconds):
        self.current += timedelta(
            seconds=seconds
        )


def make_presence(
    value,
    clock,
    *,
    location_id="living",
):
    observation = Observation.create(
        "presence",
        value,
        location_id=location_id,
    )

    return replace(
        observation,
        observed_at=clock.now().isoformat(),
    )


def make_pipeline(household_state):
    return PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            PresenceInterpreter(),
        ],
        capabilities=[
            OccupancyCapability(),
        ],
    )


def test_fresh_presence_produces_occupied_household_state():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    presence = make_presence(
        True,
        clock,
    )

    observations = accumulator.update(
        [presence]
    )

    entries = pipeline.process(
        observations
    )

    assert len(entries) == 1

    entry = household_state.get(
        "occupancy",
        location_id="living",
    )

    assert entry is not None
    assert entry.value == {
        "state": "occupied",
        "count": None,
    }


def test_stale_presence_produces_no_new_occupancy_state():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    presence = make_presence(
        True,
        clock,
    )

    accumulator.update(
        [presence]
    )

    clock.advance(61)

    observations = accumulator.for_location(
        "living"
    )

    assert observations == []

    entries = pipeline.process(
        observations
    )

    assert entries == []

    assert household_state.get(
        "occupancy",
        location_id="living",
    ) is None


def test_stale_presence_is_not_interpreted_as_unoccupied():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    presence = make_presence(
        True,
        clock,
    )

    accumulator.update(
        [presence]
    )

    clock.advance(61)

    observations = accumulator.for_location(
        "living"
    )

    interpretations = (
        PresenceInterpreter().interpret(
            observations
        )
    )

    assert interpretations == []

    assert not any(
        interpretation.name == "unoccupied"
        for interpretation in interpretations
    )


def test_explicit_false_presence_produces_unoccupied_state():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    presence = make_presence(
        False,
        clock,
    )

    observations = accumulator.update(
        [presence]
    )

    pipeline.process(
        observations
    )

    entry = household_state.get(
        "occupancy",
        location_id="living",
    )

    assert entry is not None

    assert entry.value == {
        "state": "unoccupied",
        "count": 0,
    }

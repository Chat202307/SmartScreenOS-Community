from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.smartscreen_platform.capabilities.occupancy import (
    OccupancyCapability,
)
from src.smartscreen_platform.contracts import Observation
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
            13,
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


def presence(value, clock, *, location_id="living"):
    item = Observation.create(
        "presence",
        value,
        location_id=location_id,
    )

    return replace(
        item,
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


def test_occupancy_exists_while_presence_is_fresh():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    household_state = HouseholdStateEngine(
        clock=clock.now,
    )
    pipeline = make_pipeline(
        household_state
    )

    observations = accumulator.update([
        presence(
            True,
            clock,
        ),
    ])

    pipeline.process(
        observations
    )

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is not None
    )


def test_occupancy_is_withdrawn_when_last_observation_expires():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    household_state = HouseholdStateEngine(
        clock=clock.now,
    )
    pipeline = make_pipeline(
        household_state
    )

    accumulator.update([
        presence(
            True,
            clock,
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "living"
        )
    )

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is not None
    )

    clock.advance(61)

    observations = accumulator.for_location(
        "living"
    )

    assert observations == []

    pipeline.process(
        observations,
        location_id="living",
    )

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is None
    )


def test_empty_observations_without_location_are_noop():
    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    pipeline.process([
        Observation.create(
            "presence",
            True,
            location_id="living",
        ),
    ])

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is not None
    )

    result = pipeline.process([])

    assert result == []

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is not None
    )


def test_empty_location_withdrawal_is_location_scoped():
    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    pipeline.process([
        Observation.create(
            "presence",
            True,
            location_id="living",
        ),
        Observation.create(
            "presence",
            True,
            location_id="bedroom",
        ),
    ])

    pipeline.process(
        [],
        location_id="living",
    )

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is None
    )

    assert (
        household_state.get(
            "occupancy",
            location_id="bedroom",
        )
        is not None
    )

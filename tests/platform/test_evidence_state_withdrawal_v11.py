from dataclasses import replace
from datetime import datetime, timedelta, timezone

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


def observation(
    parameter,
    value,
    clock,
    *,
    location_id="living",
    unit=None,
):
    item = Observation.create(
        parameter,
        value,
        unit=unit,
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
            ThermalInterpreter(),
        ],
        capabilities=[
            ComfortCapability(),
        ],
    )


def test_comfort_exists_while_required_evidence_is_fresh():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "temperature"): 300,
            ("living", "humidity"): 60,
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
        observation(
            "temperature",
            25,
            clock,
            unit="degC",
        ),
        observation(
            "humidity",
            50,
            clock,
            unit="percent",
        ),
    ])

    entries = pipeline.process(
        observations
    )

    assert len(entries) == 1

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is not None
    )


def test_comfort_is_withdrawn_when_required_humidity_expires():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "temperature"): 300,
            ("living", "humidity"): 60,
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
        observation(
            "temperature",
            25,
            clock,
            unit="degC",
        ),
        observation(
            "humidity",
            50,
            clock,
            unit="percent",
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "living"
        )
    )

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is not None
    )

    clock.advance(61)

    observations = accumulator.for_location(
        "living"
    )

    assert [
        item.parameter
        for item in observations
    ] == [
        "temperature",
    ]

    pipeline.process(
        observations
    )

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is None
    )


def test_temperature_only_after_humidity_expiry_does_not_refresh_comfort():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "temperature"): 300,
            ("living", "humidity"): 60,
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
        observation(
            "temperature",
            25,
            clock,
            unit="degC",
        ),
        observation(
            "humidity",
            50,
            clock,
            unit="percent",
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "living"
        )
    )

    original = household_state.get(
        "comfort",
        location_id="living",
    )

    assert original is not None

    clock.advance(61)

    accumulator.update([
        observation(
            "temperature",
            26,
            clock,
            unit="degC",
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "living"
        )
    )

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is None
    )

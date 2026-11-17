from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.smartscreen_platform.capabilities.comfort import (
    ComfortCapability,
)
from src.smartscreen_platform.capabilities.occupancy import (
    OccupancyCapability,
)
from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)
from src.smartscreen_platform.interpretation import (
    PresenceInterpreter,
    ThermalInterpreter,
)
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)
from src.smartscreen_platform.freshness_sweep import (
    ObservationFreshnessSweep,
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
            PresenceInterpreter(),
        ],
        capabilities=[
            ComfortCapability(),
            OccupancyCapability(),
        ],
    )


def test_sweep_withdraws_occupancy_when_presence_expires():
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
        observation(
            "presence",
            True,
            clock,
        ),
    ])

    pipeline.process(
        accumulator.for_location("living"),
        location_id="living",
    )

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is not None
    )

    clock.advance(61)

    sweep = ObservationFreshnessSweep(
        accumulator=accumulator,
        observation_sink=pipeline,
    )

    sweep.run_once()

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is None
    )


def test_sweep_withdraws_comfort_when_humidity_expires():
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
        accumulator.for_location("living"),
        location_id="living",
    )

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is not None
    )

    clock.advance(61)

    sweep = ObservationFreshnessSweep(
        accumulator=accumulator,
        observation_sink=pipeline,
    )

    sweep.run_once()

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is None
    )


def test_sweep_is_location_scoped():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
            ("bedroom", "presence"): 300,
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
            "presence",
            True,
            clock,
            location_id="living",
        ),
    ])

    accumulator.update([
        observation(
            "presence",
            True,
            clock,
            location_id="bedroom",
        ),
    ])

    pipeline.process(
        accumulator.for_location("living"),
        location_id="living",
    )
    pipeline.process(
        accumulator.for_location("bedroom"),
        location_id="bedroom",
    )

    clock.advance(61)

    sweep = ObservationFreshnessSweep(
        accumulator=accumulator,
        observation_sink=pipeline,
    )

    sweep.run_once()

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


def test_sweep_handles_no_known_locations():
    accumulator = ObservationAccumulator()

    class Sink:
        def __init__(self):
            self.calls = []

        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            self.calls.append(
                (
                    list(observations),
                    location_id,
                )
            )

    sink = Sink()

    sweep = ObservationFreshnessSweep(
        accumulator=accumulator,
        observation_sink=sink,
    )

    assert sweep.run_once() == 0
    assert sink.calls == []


def test_sweep_background_lifecycle():
    from threading import Event

    swept = Event()

    class Accumulator:
        def __init__(self):
            self.calls = 0

        def locations(self):
            self.calls += 1
            swept.set()
            return []

    class Sink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            pass

    accumulator = Accumulator()

    sweep = ObservationFreshnessSweep(
        accumulator=accumulator,
        observation_sink=Sink(),
        interval_seconds=0.01,
    )

    sweep.start()
    try:
        assert swept.wait(timeout=10.0), "background freshness sweep did not execute"
    finally:
        sweep.stop()
        sweep.join(timeout=5.0)

    assert accumulator.calls >= 1
    assert not sweep._thread.is_alive()


def test_sweep_start_is_idempotent():
    class Accumulator:
        def locations(self):
            return []

    class Sink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            pass

    sweep = ObservationFreshnessSweep(
        accumulator=Accumulator(),
        observation_sink=Sink(),
        interval_seconds=60,
    )

    sweep.start()

    first_thread = sweep._thread

    sweep.start()

    assert sweep._thread is first_thread

    sweep.stop()
    sweep.join(timeout=1.0)

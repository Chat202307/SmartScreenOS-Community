from dataclasses import replace

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from src.smartscreen_platform.capabilities.weather_advice import (
    WeatherAdviceCapability,
)
from src.smartscreen_platform.contracts import (
    Observation,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
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
    unit=None,
):
    item = Observation.create(
        parameter,
        value,
        unit=unit,
        location_id="outdoor",
    )

    return replace(
        item,
        observed_at=clock.now().isoformat(),
    )


def make_pipeline(household_state):
    return PlatformStatePipeline(
        household_state=household_state,
        interpreters=[],
        capabilities=[
            WeatherAdviceCapability(),
        ],
    )


def test_weather_advice_is_written_to_household_state():
    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    entries = pipeline.process([
        Observation.create(
            "precipitation_probability",
            80,
            unit="percent",
            location_id="outdoor",
        ),
        Observation.create(
            "apparent_temperature",
            7,
            unit="degC",
            location_id="outdoor",
        ),
    ])

    assert len(entries) == 2

    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is not None
    )

    assert (
        household_state.get(
            "clothing_advice",
            location_id="outdoor",
        )
        is not None
    )


def test_umbrella_advice_is_withdrawn_when_rain_evidence_expires():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            (
                "outdoor",
                "precipitation_probability",
            ): 60,
            (
                "outdoor",
                "apparent_temperature",
            ): 300,
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
            "precipitation_probability",
            80,
            clock,
            unit="percent",
        ),
        observation(
            "apparent_temperature",
            12,
            clock,
            unit="degC",
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "outdoor"
        )
    )

    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is not None
    )

    clock.advance(61)

    observations = accumulator.for_location(
        "outdoor"
    )

    pipeline.process(
        observations,
        location_id="outdoor",
    )

    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is None
    )

    assert (
        household_state.get(
            "clothing_advice",
            location_id="outdoor",
        )
        is not None
    )


def test_clothing_advice_is_withdrawn_when_temperature_evidence_expires():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            (
                "outdoor",
                "precipitation_probability",
            ): 300,
            (
                "outdoor",
                "apparent_temperature",
            ): 60,
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
            "precipitation_probability",
            20,
            clock,
            unit="percent",
        ),
        observation(
            "apparent_temperature",
            7,
            clock,
            unit="degC",
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "outdoor"
        )
    )

    assert (
        household_state.get(
            "clothing_advice",
            location_id="outdoor",
        )
        is not None
    )

    clock.advance(61)

    pipeline.process(
        accumulator.for_location(
            "outdoor"
        ),
        location_id="outdoor",
    )

    assert (
        household_state.get(
            "clothing_advice",
            location_id="outdoor",
        )
        is None
    )

    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is not None
    )


def test_all_weather_advice_is_withdrawn_when_location_becomes_empty():
    household_state = HouseholdStateEngine()
    pipeline = make_pipeline(
        household_state
    )

    pipeline.process([
        Observation.create(
            "precipitation_probability",
            80,
            unit="percent",
            location_id="outdoor",
        ),
        Observation.create(
            "apparent_temperature",
            7,
            unit="degC",
            location_id="outdoor",
        ),
    ])

    pipeline.process(
        [],
        location_id="outdoor",
    )

    assert (
        household_state.get(
            "umbrella_advice",
            location_id="outdoor",
        )
        is None
    )

    assert (
        household_state.get(
            "clothing_advice",
            location_id="outdoor",
        )
        is None
    )


def test_forecast_precipitation_advice_is_withdrawn_when_evidence_expires():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            (
                "outdoor",
                "forecast_precipitation",
            ): 60,
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
            "forecast_precipitation",
            0.4,
            clock,
            unit="mm",
        ),
    ])

    pipeline.process(
        accumulator.for_location(
            "outdoor"
        ),
        location_id="outdoor",
    )

    assert any(
        item["target"] == "umbrella_advice"
        and item["location_id"] == "outdoor"
        for item in household_state.snapshot()
    )

    clock.advance(
        seconds=61
    )

    pipeline.process(
        accumulator.for_location(
            "outdoor"
        ),
        location_id="outdoor",
    )

    assert all(
        not (
            item["target"] == "umbrella_advice"
            and item["location_id"] == "outdoor"
        )
        for item in household_state.snapshot()
    )

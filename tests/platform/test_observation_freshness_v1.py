from dataclasses import replace
from datetime import datetime, timedelta, timezone

from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
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


def make_observation(
    parameter,
    value,
    clock,
    *,
    location_id="living",
):
    observation = Observation.create(
        parameter,
        value,
        location_id=location_id,
    )

    return replace(
        observation,
        observed_at=clock.now().isoformat(),
    )


def test_accumulator_keeps_fresh_observation():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=60,
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(59)

    assert accumulator.for_location(
        "living"
    ) == [
        temperature,
    ]


def test_accumulator_removes_stale_observation():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=60,
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == []


def test_update_does_not_return_stale_previous_parameter():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=60,
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(61)

    humidity = make_observation(
        "humidity",
        75,
        clock,
    )

    current = accumulator.update(
        [humidity]
    )

    assert current == [
        humidity,
    ]


def test_freshness_isolated_between_parameters():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=60,
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(40)

    humidity = make_observation(
        "humidity",
        75,
        clock,
    )

    accumulator.update(
        [humidity]
    )

    clock.advance(30)

    assert accumulator.for_location(
        "living"
    ) == [
        humidity,
    ]


def test_default_accumulator_preserves_existing_behavior():
    clock = FakeClock()

    accumulator = ObservationAccumulator()

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(3600)

    assert accumulator.for_location(
        "living"
    ) == [
        temperature,
    ]


def test_accumulator_rejects_non_positive_max_age():
    for value in (
        0,
        -1,
    ):
        try:
            ObservationAccumulator(
                max_age_seconds=value
            )
        except ValueError as exc:
            assert str(exc) == (
                "max_age_seconds must be greater than zero"
            )
        else:
            raise AssertionError(
                "Expected ValueError"
            )


def test_accumulator_supports_parameter_specific_max_age():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_parameter={
            "temperature": 300,
            "presence": 60,
        },
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    presence = make_observation(
        "presence",
        True,
        clock,
    )

    accumulator.update(
        [
            temperature,
            presence,
        ]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == [
        temperature,
    ]


def test_parameter_max_age_overrides_default_max_age():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=300,
        max_age_by_parameter={
            "presence": 60,
        },
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    presence = make_observation(
        "presence",
        True,
        clock,
    )

    accumulator.update(
        [
            temperature,
            presence,
        ]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == [
        temperature,
    ]


def test_unconfigured_parameter_uses_default_max_age():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=60,
        max_age_by_parameter={
            "presence": 300,
        },
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == []


def test_unconfigured_parameter_without_default_does_not_expire():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_parameter={
            "presence": 60,
        },
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(3600)

    assert accumulator.for_location(
        "living"
    ) == [
        temperature,
    ]


def test_accumulator_rejects_invalid_parameter_max_age():
    invalid_policies = (
        {
            "presence": 0,
        },
        {
            "presence": -1,
        },
    )

    for policy in invalid_policies:
        try:
            ObservationAccumulator(
                max_age_by_parameter=policy
            )
        except ValueError as exc:
            assert str(exc) == (
                "parameter max age must be greater than zero"
            )
        else:
            raise AssertionError(
                "Expected ValueError"
            )


def test_parameter_freshness_does_not_convert_stale_presence_to_false():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_parameter={
            "presence": 60,
        },
        clock=clock.now,
    )

    presence = make_observation(
        "presence",
        True,
        clock,
    )

    accumulator.update(
        [presence]
    )

    clock.advance(61)

    current = accumulator.for_location(
        "living"
    )

    assert current == []

    assert not any(
        observation.parameter == "presence"
        and observation.value is False
        for observation in current
    )


def test_observation_is_fresh_at_exact_max_age_boundary():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_seconds=60,
        clock=clock.now,
    )

    temperature = make_observation(
        "temperature",
        31,
        clock,
    )

    accumulator.update(
        [temperature]
    )

    clock.advance(60)

    assert accumulator.for_location(
        "living"
    ) == [
        temperature,
    ]


def test_parameter_observation_is_fresh_at_exact_max_age_boundary():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_parameter={
            "presence": 60,
        },
        clock=clock.now,
    )

    presence = make_observation(
        "presence",
        True,
        clock,
    )

    accumulator.update(
        [presence]
    )

    clock.advance(60)

    assert accumulator.for_location(
        "living"
    ) == [
        presence,
    ]


def test_accumulator_rejects_invalid_parameter_policy_value_type():
    invalid_policies = (
        {
            "presence": None,
        },
        {
            "presence": "60",
        },
    )

    for policy in invalid_policies:
        try:
            ObservationAccumulator(
                max_age_by_parameter=policy
            )
        except ValueError as exc:
            assert str(exc) == (
                "parameter max age must be a positive number"
            )
        else:
            raise AssertionError(
                "Expected ValueError"
            )


def test_location_parameter_policy_supports_different_max_age():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
            ("bedroom", "presence"): 120,
        },
        clock=clock.now,
    )

    living_presence = make_observation(
        "presence",
        True,
        clock,
        location_id="living",
    )

    bedroom_presence = make_observation(
        "presence",
        True,
        clock,
        location_id="bedroom",
    )

    accumulator.update(
        [living_presence]
    )

    accumulator.update(
        [bedroom_presence]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == []

    assert accumulator.for_location(
        "bedroom"
    ) == [
        bedroom_presence,
    ]


def test_location_parameter_policy_overrides_parameter_policy():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_parameter={
            "presence": 300,
        },
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    living_presence = make_observation(
        "presence",
        True,
        clock,
        location_id="living",
    )

    bedroom_presence = make_observation(
        "presence",
        True,
        clock,
        location_id="bedroom",
    )

    accumulator.update(
        [living_presence]
    )

    accumulator.update(
        [bedroom_presence]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == []

    assert accumulator.for_location(
        "bedroom"
    ) == [
        bedroom_presence,
    ]


def test_parameter_policy_remains_global_fallback():
    clock = FakeClock()

    accumulator = ObservationAccumulator(
        max_age_by_parameter={
            "temperature": 60,
        },
        max_age_by_location_parameter={
            ("living", "presence"): 30,
        },
        clock=clock.now,
    )

    bedroom_temperature = make_observation(
        "temperature",
        23,
        clock,
        location_id="bedroom",
    )

    accumulator.update(
        [bedroom_temperature]
    )

    clock.advance(61)

    assert accumulator.for_location(
        "bedroom"
    ) == []


def test_location_parameter_policy_rejects_invalid_max_age():
    invalid_policies = (
        {
            ("living", "presence"): 0,
        },
        {
            ("living", "presence"): -1,
        },
        {
            ("living", "presence"): None,
        },
        {
            ("living", "presence"): "60",
        },
        {
            ("living", "presence"): True,
        },
    )

    for policy in invalid_policies:
        try:
            ObservationAccumulator(
                max_age_by_location_parameter=policy
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Expected ValueError"
            )

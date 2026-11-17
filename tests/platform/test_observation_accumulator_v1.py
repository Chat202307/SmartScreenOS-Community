from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
)


def make_observation(
    parameter,
    value,
    *,
    location_id="living",
):
    return Observation.create(
        parameter,
        value,
        location_id=location_id,
    )


def test_accumulator_returns_latest_observations_for_location():
    accumulator = ObservationAccumulator()

    temperature = make_observation(
        "temperature",
        31,
    )
    humidity = make_observation(
        "humidity",
        75,
    )

    first = accumulator.update(
        [temperature]
    )

    assert first == [
        temperature,
    ]

    second = accumulator.update(
        [humidity]
    )

    assert second == [
        temperature,
        humidity,
    ]


def test_accumulator_replaces_previous_parameter_value():
    accumulator = ObservationAccumulator()

    old_temperature = make_observation(
        "temperature",
        25,
    )
    new_temperature = make_observation(
        "temperature",
        31,
    )

    accumulator.update(
        [old_temperature]
    )

    current = accumulator.update(
        [new_temperature]
    )

    assert current == [
        new_temperature,
    ]

    assert (
        old_temperature.observation_id
        not in {
            item.observation_id
            for item in current
        }
    )


def test_accumulator_keeps_locations_isolated():
    accumulator = ObservationAccumulator()

    living_temperature = make_observation(
        "temperature",
        31,
        location_id="living",
    )

    bedroom_temperature = make_observation(
        "temperature",
        23,
        location_id="bedroom",
    )

    accumulator.update(
        [living_temperature]
    )

    current = accumulator.update(
        [bedroom_temperature]
    )

    assert current == [
        bedroom_temperature,
    ]

    assert accumulator.for_location(
        "living"
    ) == [
        living_temperature,
    ]

    assert accumulator.for_location(
        "bedroom"
    ) == [
        bedroom_temperature,
    ]


def test_accumulator_keeps_parameters_isolated():
    accumulator = ObservationAccumulator()

    temperature = make_observation(
        "temperature",
        31,
    )

    humidity = make_observation(
        "humidity",
        75,
    )

    accumulator.update(
        [
            temperature,
            humidity,
        ]
    )

    current = accumulator.for_location(
        "living"
    )

    assert {
        item.parameter
        for item in current
    } == {
        "temperature",
        "humidity",
    }


def test_accumulator_update_rejects_mixed_locations():
    accumulator = ObservationAccumulator()

    living_temperature = make_observation(
        "temperature",
        31,
        location_id="living",
    )

    bedroom_humidity = make_observation(
        "humidity",
        45,
        location_id="bedroom",
    )

    try:
        accumulator.update(
            [
                living_temperature,
                bedroom_humidity,
            ]
        )
    except ValueError as exc:
        assert str(exc) == (
            "observations must share location_id"
        )
    else:
        raise AssertionError(
            "Expected ValueError for mixed locations"
        )


def test_accumulator_supports_none_location():
    accumulator = ObservationAccumulator()

    temperature = make_observation(
        "temperature",
        24,
        location_id=None,
    )

    assert accumulator.update(
        [temperature]
    ) == [
        temperature,
    ]

    assert accumulator.for_location(
        None
    ) == [
        temperature,
    ]


def test_empty_update_returns_empty():
    accumulator = ObservationAccumulator()

    assert accumulator.update([]) == []


def test_accumulator_exposes_known_locations():
    accumulator = ObservationAccumulator()

    accumulator.update([
        make_observation(
            "temperature",
            25,
            location_id="living",
        ),
    ])

    accumulator.update([
        make_observation(
            "presence",
            True,
            location_id="bedroom",
        ),
    ])

    assert set(
        accumulator.locations()
    ) == {
        "living",
        "bedroom",
    }


def test_accumulator_keeps_location_known_after_last_observation_expires():
    from datetime import datetime, timedelta, timezone
    from dataclasses import replace

    class LocalClock:
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

    clock = LocalClock()

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("living", "presence"): 60,
        },
        clock=clock.now,
    )

    accumulator.update([
        replace(
            make_observation(
                "presence",
                True,
                location_id="living",
            ),
            observed_at=clock.now().isoformat(),
        ),
    ])

    clock.advance(61)

    assert accumulator.for_location(
        "living"
    ) == []

    assert accumulator.locations() == [
        "living",
    ]


def test_observation_accumulator_snapshot_returns_all_locations():
    accumulator = ObservationAccumulator()

    living = make_observation(
        "temperature",
        24,
        location_id="living",
    )

    corridor = make_observation(
        "illuminance",
        45,
        location_id="corridor",
    )

    accumulator.update(
        [living]
    )

    accumulator.update(
        [corridor]
    )

    snapshot = accumulator.snapshot()

    assert {
        item.observation_id
        for item in snapshot
    } == {
        living.observation_id,
        corridor.observation_id,
    }


def test_observation_accumulator_snapshot_removes_stale_observations():
    from datetime import (
        datetime,
        timedelta,
        timezone,
    )

    now = datetime(
        2026,
        8,
        15,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter={
            ("corridor", "illuminance"): 60,
        },
        clock=lambda: now,
    )

    old = make_observation(
        "illuminance",
        45,
        location_id="corridor",
    )

    object.__setattr__(
        old,
        "observed_at",
        (
            now
            - timedelta(seconds=120)
        ).isoformat(),
    )

    accumulator.update(
        [old]
    )

    assert accumulator.snapshot() == []


def test_accumulator_can_withdraw_one_parameter():
    from src.smartscreen_platform.contracts import (
        Observation,
    )
    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )

    accumulator = ObservationAccumulator()

    presence = Observation.create(
        parameter="presence",
        value=True,
        location_id="living",
    )

    illuminance = Observation.create(
        parameter="illuminance",
        value=49.0,
        unit="lux",
        location_id="living",
    )

    accumulator.update(
        [
            presence,
            illuminance,
        ]
    )

    remaining = accumulator.withdraw(
        "living",
        "illuminance",
    )

    assert remaining == [
        presence
    ]

    assert accumulator.for_location(
        "living"
    ) == [
        presence
    ]


def test_accumulator_withdraw_missing_parameter_is_noop():
    from src.smartscreen_platform.contracts import (
        Observation,
    )
    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )

    accumulator = ObservationAccumulator()

    presence = Observation.create(
        parameter="presence",
        value=True,
        location_id="living",
    )

    accumulator.update(
        [
            presence,
        ]
    )

    remaining = accumulator.withdraw(
        "living",
        "illuminance",
    )

    assert remaining == [
        presence
    ]

    assert accumulator.for_location(
        "living"
    ) == [
        presence
    ]


def test_accumulator_withdraw_is_location_scoped():
    from src.smartscreen_platform.contracts import (
        Observation,
    )
    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )

    accumulator = ObservationAccumulator()

    living = Observation.create(
        parameter="illuminance",
        value=49.0,
        unit="lux",
        location_id="living",
    )

    corridor = Observation.create(
        parameter="illuminance",
        value=20.0,
        unit="lux",
        location_id="corridor",
    )

    accumulator.update(
        [
            living,
        ]
    )

    accumulator.update(
        [
            corridor,
        ]
    )

    remaining = accumulator.withdraw(
        "living",
        "illuminance",
    )

    assert remaining == []

    assert accumulator.for_location(
        "living"
    ) == []

    assert accumulator.for_location(
        "corridor"
    ) == [
        corridor
    ]

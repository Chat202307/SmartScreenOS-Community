from datetime import datetime, timedelta, timezone
from dataclasses import replace

from src.smartscreen_platform.contracts import StatePatch
from src.smartscreen_platform.household_state import (
    HouseholdStateChangeNotifier,
    HouseholdStateEngine,
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
            seconds=seconds,
        )


def make_patch(
    value,
    *,
    confidence=0.8,
    ttl_seconds=60,
    created_at=None,
):
    patch = StatePatch.create(
        capability="occupancy",
        target="occupancy",
        value=value,
        confidence=confidence,
        ttl_seconds=ttl_seconds,
        location_id="living",
    )

    if created_at is not None:
        patch = replace(
            patch,
            created_at=created_at,
        )

    return patch


def test_notifier_starts_at_revision_zero():
    notifier = HouseholdStateChangeNotifier()

    assert notifier.revision == 0


def test_accepted_patch_increments_revision():
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        change_notifier=notifier,
    )

    engine.apply(
        make_patch(
            {
                "state": "occupied",
                "count": None,
            }
        )
    )

    assert notifier.revision == 1


def test_each_accepted_patch_increments_revision():
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        change_notifier=notifier,
    )

    engine.apply(
        make_patch(
            {
                "state": "occupied",
                "count": None,
            },
            confidence=0.8,
        )
    )

    engine.apply(
        make_patch(
            {
                "state": "unoccupied",
                "count": 0,
            },
            confidence=0.9,
        )
    )

    assert notifier.revision == 2


def test_rejected_lower_confidence_patch_does_not_increment_revision():
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        change_notifier=notifier,
    )

    engine.apply(
        make_patch(
            {
                "state": "occupied",
                "count": None,
            },
            confidence=0.9,
        )
    )

    engine.apply(
        make_patch(
            {
                "state": "unoccupied",
                "count": 0,
            },
            confidence=0.5,
        )
    )

    assert notifier.revision == 1


def test_snapshot_expiry_increments_revision():
    clock = FakeClock()
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        clock=clock.now,
        change_notifier=notifier,
    )

    engine.apply(
        make_patch(
            {
                "state": "occupied",
                "count": None,
            },
            ttl_seconds=60,
            created_at=clock.now().isoformat(),
        )
    )

    assert notifier.revision == 1

    clock.advance(61)

    assert engine.snapshot() == []
    assert notifier.revision == 2


def test_get_expiry_increments_revision():
    clock = FakeClock()
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        clock=clock.now,
        change_notifier=notifier,
    )

    engine.apply(
        make_patch(
            {
                "state": "occupied",
                "count": None,
            },
            ttl_seconds=60,
            created_at=clock.now().isoformat(),
        )
    )

    clock.advance(61)

    assert (
        engine.get(
            "occupancy",
            location_id="living",
        )
        is None
    )

    assert notifier.revision == 2


def test_notifier_wait_returns_after_revision_change():
    notifier = HouseholdStateChangeNotifier()

    original = notifier.revision

    notifier.notify()

    assert (
        notifier.wait_for_change(
            original,
            timeout=0,
        )
        == original + 1
    )


def test_replacing_expired_entry_increments_revision_once():
    clock = FakeClock()
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        clock=clock.now,
        change_notifier=notifier,
    )

    engine.apply(
        make_patch(
            {
                "state": "occupied",
                "count": None,
            },
            confidence=0.8,
            ttl_seconds=60,
            created_at=clock.now().isoformat(),
        )
    )

    assert notifier.revision == 1

    clock.advance(61)

    engine.apply(
        make_patch(
            {
                "state": "unoccupied",
                "count": 0,
            },
            confidence=0.8,
            ttl_seconds=60,
            created_at=clock.now().isoformat(),
        )
    )

    assert notifier.revision == 2

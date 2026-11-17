from datetime import datetime, timedelta, timezone

from src.smartscreen_platform.contracts.state import (
    StatePatch,
)
from src.smartscreen_platform.household_state import (
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
            seconds=seconds
        )


def make_patch(
    clock,
    *,
    target="occupancy",
    value=None,
    ttl_seconds=60,
    location_id="living",
):
    if value is None:
        value = {
            "state": "occupied",
            "count": None,
        }

    patch = StatePatch.create(
        capability="occupancy",
        target=target,
        value=value,
        confidence=1.0,
        ttl_seconds=ttl_seconds,
        location_id=location_id,
    )

    return patch.__class__(
        capability=patch.capability,
        target=patch.target,
        value=patch.value,
        confidence=patch.confidence,
        ttl_seconds=patch.ttl_seconds,
        created_at=clock.now().isoformat(),
        location_id=patch.location_id,
        evidence_refs=patch.evidence_refs,
        metadata=patch.metadata,
    )


def test_get_returns_fresh_household_state_entry():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    patch = make_patch(
        clock,
        ttl_seconds=60,
    )

    engine.apply(patch)

    clock.advance(59)

    entry = engine.get(
        "occupancy",
        location_id="living",
    )

    assert entry is not None
    assert entry.value["state"] == "occupied"


def test_get_removes_expired_household_state_entry():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    patch = make_patch(
        clock,
        ttl_seconds=60,
    )

    engine.apply(patch)

    clock.advance(61)

    assert (
        engine.get(
            "occupancy",
            location_id="living",
        )
        is None
    )


def test_snapshot_excludes_expired_household_state_entry():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    patch = make_patch(
        clock,
        ttl_seconds=60,
    )

    engine.apply(patch)

    clock.advance(61)

    assert engine.snapshot() == []


def test_expiration_isolated_between_entries():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    engine.apply(
        make_patch(
            clock,
            target="occupancy",
            ttl_seconds=60,
        )
    )

    engine.apply(
        make_patch(
            clock,
            target="comfort",
            value={
                "level": "comfortable",
            },
            ttl_seconds=300,
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

    comfort = engine.get(
        "comfort",
        location_id="living",
    )

    assert comfort is not None
    assert comfort.value == {
        "level": "comfortable",
    }


def test_expiration_isolated_between_locations():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    engine.apply(
        make_patch(
            clock,
            location_id="living",
            ttl_seconds=60,
        )
    )

    clock.advance(30)

    engine.apply(
        make_patch(
            clock,
            location_id="bedroom",
            ttl_seconds=60,
        )
    )

    clock.advance(31)

    assert (
        engine.get(
            "occupancy",
            location_id="living",
        )
        is None
    )

    bedroom = engine.get(
        "occupancy",
        location_id="bedroom",
    )

    assert bedroom is not None
    assert bedroom.location_id == "bedroom"


def test_entry_is_fresh_at_ttl_boundary():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    engine.apply(
        make_patch(
            clock,
            ttl_seconds=60,
        )
    )

    clock.advance(60)

    assert (
        engine.get(
            "occupancy",
            location_id="living",
        )
        is not None
    )


def test_entry_expires_after_ttl_boundary():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    engine.apply(
        make_patch(
            clock,
            ttl_seconds=60,
        )
    )

    clock.advance(60.001)

    assert (
        engine.get(
            "occupancy",
            location_id="living",
        )
        is None
    )


def test_expired_entry_does_not_block_lower_confidence_patch():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    old_patch = StatePatch.create(
        capability="occupancy",
        target="occupancy",
        value={
            "state": "occupied",
            "count": None,
        },
        confidence=1.0,
        ttl_seconds=60,
        location_id="living",
    )

    old_patch = old_patch.__class__(
        capability=old_patch.capability,
        target=old_patch.target,
        value=old_patch.value,
        confidence=old_patch.confidence,
        ttl_seconds=old_patch.ttl_seconds,
        created_at=clock.now().isoformat(),
        location_id=old_patch.location_id,
        evidence_refs=old_patch.evidence_refs,
        metadata=old_patch.metadata,
    )

    engine.apply(old_patch)

    clock.advance(61)

    new_patch = StatePatch.create(
        capability="occupancy",
        target="occupancy",
        value={
            "state": "unoccupied",
            "count": 0,
        },
        confidence=0.8,
        ttl_seconds=60,
        location_id="living",
    )

    new_patch = new_patch.__class__(
        capability=new_patch.capability,
        target=new_patch.target,
        value=new_patch.value,
        confidence=new_patch.confidence,
        ttl_seconds=new_patch.ttl_seconds,
        created_at=clock.now().isoformat(),
        location_id=new_patch.location_id,
        evidence_refs=new_patch.evidence_refs,
        metadata=new_patch.metadata,
    )

    applied = engine.apply(
        new_patch
    )

    assert applied.value == {
        "state": "unoccupied",
        "count": 0,
    }

    assert applied.confidence == 0.8

    current = engine.get(
        "occupancy",
        location_id="living",
    )

    assert current is not None
    assert current.value == {
        "state": "unoccupied",
        "count": 0,
    }


def test_fresh_entry_still_blocks_lower_confidence_patch():
    clock = FakeClock()

    engine = HouseholdStateEngine(
        clock=clock.now,
    )

    old_patch = make_patch(
        clock,
        ttl_seconds=60,
    )

    engine.apply(old_patch)

    clock.advance(30)

    new_patch = StatePatch.create(
        capability="occupancy",
        target="occupancy",
        value={
            "state": "unoccupied",
            "count": 0,
        },
        confidence=0.8,
        ttl_seconds=60,
        location_id="living",
    )

    applied = engine.apply(
        new_patch
    )

    assert applied.value == {
        "state": "occupied",
        "count": None,
    }

    assert applied.confidence == 1.0

from src.smartscreen_platform.contracts.state import (
    StatePatch,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateChangeNotifier,
    HouseholdStateEngine,
)


def make_patch():
    return StatePatch.create(
        capability="comfort",
        target="comfort",
        value={
            "level": "comfortable",
            "score": 100,
        },
        confidence=0.9,
        ttl_seconds=300,
        location_id="living",
    )


def test_household_state_can_remove_existing_state():
    engine = HouseholdStateEngine()

    engine.apply(
        make_patch()
    )

    assert (
        engine.get(
            "comfort",
            location_id="living",
        )
        is not None
    )

    removed = engine.remove(
        "comfort",
        location_id="living",
    )

    assert removed is True

    assert (
        engine.get(
            "comfort",
            location_id="living",
        )
        is None
    )


def test_removing_missing_state_is_noop():
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        change_notifier=notifier,
    )

    removed = engine.remove(
        "comfort",
        location_id="living",
    )

    assert removed is False
    assert notifier.revision == 0


def test_removing_existing_state_notifies_change():
    notifier = HouseholdStateChangeNotifier()

    engine = HouseholdStateEngine(
        change_notifier=notifier,
    )

    engine.apply(
        make_patch()
    )

    assert notifier.revision == 1

    removed = engine.remove(
        "comfort",
        location_id="living",
    )

    assert removed is True
    assert notifier.revision == 2

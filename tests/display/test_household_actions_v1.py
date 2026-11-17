from src.smartscreen_display.household_actions import (
    HouseholdActionExecutor,
)


ALL_LIGHTS_OFF_TARGETS = (
    "corridor.light_1",
    "living.main_light_power_1",
    "living.light_strip_1",
    "living.downlight_1",
    "dining.light_power_1",
    "dining.atmosphere_light_1",
    "kitchen.light_1",
    "master_bedroom.main_light_power_1",
    "master_bedroom.light_strip_1",
    "master_bedroom.downlight_1",
    "study.ceiling_light_1",
    "princess_room.ceiling_light_power_1",
    "princess_room.spotlight_1",
    "princess_room.light_strip_1",
    "master_bath.makeup_light_1",
    "master_bath.bathing_light_1",
    "guest_bath.makeup_light_1",
    "guest_bath.bathing_light_1",
)


class FakeDispatcher:
    def __init__(self, failures=None):
        self.calls = []
        self.failures = dict(
            failures or {}
        )

    def execute(
        self,
        *,
        device_id,
        control_id,
        value,
    ):
        self.calls.append(
            (
                device_id,
                control_id,
                value,
            )
        )

        error = self.failures.get(
            device_id
        )

        if error is not None:
            raise ValueError(error)

        return "ok"


def build_actions():
    all_lights_off = tuple(
        {
            "device_id": device_id,
            "control_id": "power",
            "value": False,
        }
        for device_id
        in ALL_LIGHTS_OFF_TARGETS
    )

    return {
        "all_lights_off": all_lights_off,
        "night": (
            all_lights_off
            + NIGHT_FINAL_TARGETS
        ),
        "away": (
            all_lights_off
            + AWAY_AIR_CONDITIONER_TARGETS
        ),
    }


def test_all_lights_off_dispatches_stable_device_targets():
    dispatcher = FakeDispatcher()

    executor = HouseholdActionExecutor(
        dispatcher=dispatcher,
        actions=build_actions(),
    )

    result = executor.execute(
        "all_lights_off"
    )

    assert dispatcher.calls == [
        (
            device_id,
            "power",
            False,
        )
        for device_id
        in ALL_LIGHTS_OFF_TARGETS
    ]

    assert result == {
        "action_id": "all_lights_off",
        "status": "success",
        "succeeded_device_ids": list(
            ALL_LIGHTS_OFF_TARGETS
        ),
        "failures": [],
    }


def test_all_lights_off_does_not_duplicate_downstream_lights():
    targets = {
        item["device_id"]
        for item in build_actions()[
            "all_lights_off"
        ]
    }

    assert (
        "living.main_light_1"
        not in targets
    )
    assert (
        "master_bedroom.main_light_1"
        not in targets
    )
    assert (
        "princess_room.ceiling_light_1"
        not in targets
    )

    assert (
        "dining.table_light_east"
        not in targets
    )
    assert (
        "dining.table_light_center"
        not in targets
    )
    assert (
        "dining.table_light_west"
        not in targets
    )


def test_household_action_continues_after_one_device_failure():
    dispatcher = FakeDispatcher(
        {
            "kitchen.light_1":
                "device unavailable",
        }
    )

    executor = HouseholdActionExecutor(
        dispatcher=dispatcher,
        actions=build_actions(),
    )

    result = executor.execute(
        "all_lights_off"
    )

    # Failure must not prevent the remaining
    # household targets from being attempted.
    assert len(dispatcher.calls) == 18

    assert result["status"] == (
        "partial_failure"
    )

    assert (
        "kitchen.light_1"
        not in result[
            "succeeded_device_ids"
        ]
    )

    assert result["failures"] == [
        {
            "device_id":
                "kitchen.light_1",
            "error":
                "device unavailable",
        }
    ]


def test_household_action_rejects_unknown_action():
    executor = HouseholdActionExecutor(
        dispatcher=FakeDispatcher(),
        actions=build_actions(),
    )

    try:
        executor.execute(
            "unknown_action"
        )
    except ValueError as exc:
        assert (
            "unknown household action"
            in str(exc)
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )


NIGHT_FINAL_TARGETS = (
    {
        "device_id": "master_bedroom.curtain_1",
        "control_id": "state",
        "value": "closed",
    },
    {
        "device_id": "princess_room.curtain_1",
        "control_id": "state",
        "value": "close",
    },
    {
        "device_id": "corridor.light_1",
        "control_id": "power",
        "value": True,
    },
    {
        "device_id": "master_bedroom.light_strip_1",
        "control_id": "power",
        "value": True,
    },
)


def test_night_action_uses_all_lights_off_then_night_final_state():
    actions = build_actions()

    night = actions["night"]

    assert len(night) == (
        len(ALL_LIGHTS_OFF_TARGETS)
        + len(NIGHT_FINAL_TARGETS)
    )

    assert [
        item["device_id"]
        for item in night[
            :len(ALL_LIGHTS_OFF_TARGETS)
        ]
    ] == list(
        ALL_LIGHTS_OFF_TARGETS
    )

    assert night[
        len(ALL_LIGHTS_OFF_TARGETS):
    ] == NIGHT_FINAL_TARGETS


def test_night_action_dispatches_in_required_order():
    dispatcher = FakeDispatcher()

    executor = HouseholdActionExecutor(
        dispatcher=dispatcher,
        actions=build_actions(),
    )

    result = executor.execute(
        "night"
    )

    expected_calls = [
        (
            device_id,
            "power",
            False,
        )
        for device_id
        in ALL_LIGHTS_OFF_TARGETS
    ]

    expected_calls.extend(
        (
            item["device_id"],
            item["control_id"],
            item["value"],
        )
        for item in NIGHT_FINAL_TARGETS
    )

    assert dispatcher.calls == expected_calls

    assert result["status"] == "success"
    assert result["failures"] == []


def test_night_final_lights_override_all_lights_off():
    night = build_actions()["night"]

    corridor = [
        item
        for item in night
        if item["device_id"]
        == "corridor.light_1"
    ]

    master_strip = [
        item
        for item in night
        if item["device_id"]
        == "master_bedroom.light_strip_1"
    ]

    assert corridor == [
        {
            "device_id": "corridor.light_1",
            "control_id": "power",
            "value": False,
        },
        {
            "device_id": "corridor.light_1",
            "control_id": "power",
            "value": True,
        },
    ]

    assert master_strip == [
        {
            "device_id":
                "master_bedroom.light_strip_1",
            "control_id": "power",
            "value": False,
        },
        {
            "device_id":
                "master_bedroom.light_strip_1",
            "control_id": "power",
            "value": True,
        },
    ]


def test_night_uses_each_curtain_native_control_value():
    night = build_actions()["night"]

    assert {
        "device_id": "master_bedroom.curtain_1",
        "control_id": "state",
        "value": "closed",
    } in night

    assert {
        "device_id": "princess_room.curtain_1",
        "control_id": "state",
        "value": "close",
    } in night


AWAY_AIR_CONDITIONER_TARGETS = (
    {
        "device_id": "air_conditioner_001",
        "control_id": "operating_state",
        "value": "off",
    },
    {
        "device_id":
            "master_bedroom.air_conditioner_1",
        "control_id": "operating_state",
        "value": "off",
    },
    {
        "device_id":
            "princess_room.air_conditioner_1",
        "control_id": "operating_state",
        "value": "off",
    },
    {
        "device_id":
            "study.air_conditioner_1",
        "control_id": "operating_state",
        "value": "off",
    },
)


def test_away_action_uses_all_lights_off_then_all_air_conditioners_off():
    actions = build_actions()

    away = actions["away"]

    assert len(away) == (
        len(ALL_LIGHTS_OFF_TARGETS)
        + len(AWAY_AIR_CONDITIONER_TARGETS)
    )

    assert [
        item["device_id"]
        for item in away[
            :len(ALL_LIGHTS_OFF_TARGETS)
        ]
    ] == list(
        ALL_LIGHTS_OFF_TARGETS
    )

    assert away[
        len(ALL_LIGHTS_OFF_TARGETS):
    ] == AWAY_AIR_CONDITIONER_TARGETS


def test_away_action_dispatches_all_air_conditioners_off():
    dispatcher = FakeDispatcher()

    executor = HouseholdActionExecutor(
        dispatcher=dispatcher,
        actions=build_actions(),
    )

    result = executor.execute(
        "away"
    )

    expected_calls = [
        (
            device_id,
            "power",
            False,
        )
        for device_id
        in ALL_LIGHTS_OFF_TARGETS
    ]

    expected_calls.extend(
        (
            item["device_id"],
            item["control_id"],
            item["value"],
        )
        for item
        in AWAY_AIR_CONDITIONER_TARGETS
    )

    assert dispatcher.calls == expected_calls

    assert result["status"] == "success"
    assert result["failures"] == []


def test_away_does_not_include_night_only_targets():
    away = build_actions()["away"]

    assert {
        "device_id": "master_bedroom.curtain_1",
        "control_id": "state",
        "value": "closed",
    } not in away

    assert {
        "device_id": "princess_room.curtain_1",
        "control_id": "state",
        "value": "close",
    } not in away

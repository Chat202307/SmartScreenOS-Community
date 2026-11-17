import json

from src.smartscreen_display.household_actions_config import (
    load_household_actions,
)


def test_loader_reads_household_actions(tmp_path):
    path = tmp_path / "household_actions.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "actions": {
                    "all_lights_off": [
                        {
                            "device_id":
                                "kitchen.light_1",
                            "control_id":
                                "power",
                            "value": False,
                        },
                        {
                            "device_id":
                                "corridor.light_1",
                            "control_id":
                                "power",
                            "value": False,
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    assert load_household_actions(
        path
    ) == {
        "all_lights_off": (
            {
                "device_id":
                    "kitchen.light_1",
                "control_id":
                    "power",
                "value": False,
            },
            {
                "device_id":
                    "corridor.light_1",
                "control_id":
                    "power",
                "value": False,
            },
        ),
    }


def test_loader_returns_empty_when_file_missing(
    tmp_path,
):
    assert load_household_actions(
        tmp_path / "missing.json"
    ) == {}


def test_loader_ignores_invalid_targets(tmp_path):
    path = tmp_path / "household_actions.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "actions": {
                    "all_lights_off": [
                        {
                            "device_id": "",
                            "control_id":
                                "power",
                            "value": False,
                        },
                        {
                            "device_id":
                                "kitchen.light_1",
                            "control_id": "",
                            "value": False,
                        },
                        {
                            "device_id":
                                "corridor.light_1",
                            "control_id":
                                "power",
                            "value": False,
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    assert load_household_actions(
        path
    ) == {
        "all_lights_off": (
            {
                "device_id":
                    "corridor.light_1",
                "control_id":
                    "power",
                "value": False,
            },
        ),
    }





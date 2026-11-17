import json

from src.smartscreen_display.occupancy_interpretation_config import (
    load_occupancy_interpretation_policies,
)


def test_load_motion_idle_threshold_policy(tmp_path):
    path = tmp_path / "occupancy_interpretation.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [
                    {
                        "entity_id":
                            "sensor.corridor_motion_idle",
                        "location_id": "corridor",
                        "parameter":
                            "motion_idle_seconds",
                        "strategy":
                            "motion_idle_threshold",
                        "settings": {
                            "occupied_below_seconds": 60,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert (
        load_occupancy_interpretation_policies(
            path
        )
        == [
            {
                "entity_id":
                    "sensor.corridor_motion_idle",
                "location_id": "corridor",
                "parameter":
                    "motion_idle_seconds",
                "strategy":
                    "motion_idle_threshold",
                "settings": {
                    "occupied_below_seconds": 60,
                },
            }
        ]
    )


def test_rejects_non_positive_motion_threshold(
    tmp_path,
):
    path = tmp_path / "occupancy_interpretation.json"

    path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "entity_id":
                            "sensor.invalid",
                        "location_id": "corridor",
                        "parameter":
                            "motion_idle_seconds",
                        "strategy":
                            "motion_idle_threshold",
                        "settings": {
                            "occupied_below_seconds": 0,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert (
        load_occupancy_interpretation_policies(
            path
        )
        == []
    )


def test_missing_policy_file_returns_empty(tmp_path):
    assert (
        load_occupancy_interpretation_policies(
            tmp_path / "missing.json"
        )
        == []
    )

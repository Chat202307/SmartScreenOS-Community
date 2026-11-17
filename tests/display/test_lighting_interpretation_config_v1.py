import json

from src.smartscreen_display.lighting_interpretation_config import (
    load_lighting_interpretation_knowledge,
)


def test_load_lighting_interpretation_knowledge(tmp_path):
    path = (
        tmp_path
        / "lighting_interpretation.json"
    )

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "defaults": {
                    "dim_below_lux": 80,
                    "bright_above_lux": 1200,
                },
                "locations": {
                    "corridor": {
                        "dim_below_lux": 50,
                        "bright_above_lux": 500,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    knowledge = (
        load_lighting_interpretation_knowledge(
            path
        )
    )

    assert knowledge == {
        "global": {
            "lighting_dim_below_lux": 80,
            "lighting_bright_above_lux": 1200,
        },
        "locations": {
            "corridor": {
                "lighting_dim_below_lux": 50,
                "lighting_bright_above_lux": 500,
            }
        },
    }


def test_lighting_interpretation_missing_file_returns_empty(tmp_path):
    knowledge = (
        load_lighting_interpretation_knowledge(
            tmp_path / "missing.json"
        )
    )

    assert knowledge == {
        "global": {},
        "locations": {},
    }


def test_lighting_interpretation_rejects_invalid_thresholds(
    tmp_path,
):
    path = (
        tmp_path
        / "lighting_interpretation.json"
    )

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "defaults": {
                    "dim_below_lux": 0,
                    "bright_above_lux": "1200",
                },
                "locations": {
                    "corridor": {
                        "dim_below_lux": -1,
                        "bright_above_lux": True,
                    },
                    "living": {
                        "dim_below_lux": 100,
                        "bright_above_lux": 900,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    knowledge = (
        load_lighting_interpretation_knowledge(
            path
        )
    )

    assert knowledge == {
        "global": {},
        "locations": {
            "living": {
                "lighting_dim_below_lux": 100,
                "lighting_bright_above_lux": 900,
            }
        },
    }


def test_lighting_interpretation_rejects_inverted_thresholds(
    tmp_path,
):
    path = (
        tmp_path
        / "lighting_interpretation.json"
    )

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "defaults": {
                    "dim_below_lux": 800,
                    "bright_above_lux": 500,
                },
                "locations": {
                    "corridor": {
                        "dim_below_lux": 600,
                        "bright_above_lux": 300,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    knowledge = (
        load_lighting_interpretation_knowledge(
            path
        )
    )

    assert knowledge == {
        "global": {},
        "locations": {},
    }


def test_lighting_interpretation_invalid_json_returns_empty(
    tmp_path,
):
    path = (
        tmp_path
        / "lighting_interpretation.json"
    )

    path.write_text(
        "{ invalid",
        encoding="utf-8",
    )

    assert (
        load_lighting_interpretation_knowledge(
            path
        )
        == {
            "global": {},
            "locations": {},
        }
    )


def test_lighting_interpretation_non_object_root_returns_empty(
    tmp_path,
):
    path = (
        tmp_path
        / "lighting_interpretation.json"
    )

    path.write_text(
        json.dumps(
            [
                {
                    "dim_below_lux": 80,
                    "bright_above_lux": 1200,
                }
            ]
        ),
        encoding="utf-8",
    )

    assert (
        load_lighting_interpretation_knowledge(
            path
        )
        == {
            "global": {},
            "locations": {},
        }
    )

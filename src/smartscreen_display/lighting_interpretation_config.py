from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _valid_threshold(
    value: Any,
) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(
            value,
            (int, float),
        )
        and value > 0
    )


def _load_threshold_pair(
    payload,
):
    if not isinstance(payload, dict):
        return {}

    dim = payload.get(
        "dim_below_lux"
    )

    bright = payload.get(
        "bright_above_lux"
    )

    if (
        not _valid_threshold(dim)
        or not _valid_threshold(bright)
    ):
        return {}

    if dim >= bright:
        return {}

    return {
        "lighting_dim_below_lux": dim,
        "lighting_bright_above_lux": bright,
    }


def load_lighting_interpretation_knowledge(
    path: str | Path,
) -> dict[str, Any]:
    config_path = Path(path)

    empty = {
        "global": {},
        "locations": {},
    }

    if not config_path.is_file():
        return empty

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return empty

    if not isinstance(payload, dict):
        return empty

    global_values = _load_threshold_pair(
        payload.get(
            "defaults",
            {},
        )
    )

    locations_payload = payload.get(
        "locations",
        {},
    )

    location_values = {}

    if isinstance(
        locations_payload,
        dict,
    ):
        for (
            location_id,
            settings,
        ) in locations_payload.items():
            if (
                not isinstance(
                    location_id,
                    str,
                )
                or not location_id.strip()
            ):
                continue

            values = _load_threshold_pair(
                settings
            )

            if not values:
                continue

            location_values[
                location_id
            ] = values

    return {
        "global": global_values,
        "locations": location_values,
    }

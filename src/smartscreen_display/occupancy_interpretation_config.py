from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_occupancy_interpretation_policies(
    path: str | Path,
) -> list[dict[str, Any]]:
    config_path = Path(path)

    if not config_path.is_file():
        return []

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(payload, dict):
        return []

    sources = payload.get(
        "sources",
        [],
    )

    if not isinstance(sources, list):
        return []

    valid = []

    for source in sources:
        if not isinstance(source, dict):
            continue

        entity_id = source.get(
            "entity_id"
        )
        location_id = source.get(
            "location_id"
        )
        parameter = source.get(
            "parameter"
        )
        strategy = source.get(
            "strategy"
        )
        settings = source.get(
            "settings",
            {},
        )

        if (
            not isinstance(entity_id, str)
            or not entity_id.strip()
        ):
            continue

        if (
            not isinstance(location_id, str)
            or not location_id.strip()
        ):
            continue

        if (
            not isinstance(parameter, str)
            or not parameter.strip()
        ):
            continue

        if (
            strategy
            != "motion_idle_threshold"
        ):
            continue

        if not isinstance(settings, dict):
            continue

        threshold = settings.get(
            "occupied_below_seconds"
        )

        if (
            isinstance(threshold, bool)
            or not isinstance(
                threshold,
                (int, float),
            )
            or threshold <= 0
        ):
            continue

        valid.append(
            {
                "entity_id": entity_id,
                "location_id": location_id,
                "parameter": parameter,
                "strategy": strategy,
                "settings": {
                    "occupied_below_seconds":
                        threshold,
                },
            }
        )

    return valid

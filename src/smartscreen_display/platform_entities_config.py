from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SUPPORTED_VALUE_TYPES = {
    "float",
    "int",
    "bool",
    "string",
}


def load_platform_entities(
    path: str | Path,
) -> list[dict[str, Any]]:
    """Load Home Assistant to Platform observation mappings."""

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

    entities = payload.get("entities", [])

    if not isinstance(entities, list):
        return []

    valid_entities = []

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        entity_id = entity.get("entity_id")
        parameter = entity.get("parameter")

        if (
            not isinstance(entity_id, str)
            or not entity_id.strip()
        ):
            continue

        if (
            not isinstance(parameter, str)
            or not parameter.strip()
        ):
            continue

        value_type = entity.get(
            "value_type",
            "string",
        )

        if value_type not in SUPPORTED_VALUE_TYPES:
            continue

        max_age_seconds = entity.get(
            "max_age_seconds"
        )

        if max_age_seconds is not None:
            if (
                isinstance(
                    max_age_seconds,
                    bool,
                )
                or not isinstance(
                    max_age_seconds,
                    (int, float),
                )
                or max_age_seconds <= 0
            ):
                continue

        valid_entities.append(
            dict(entity)
        )

    return valid_entities

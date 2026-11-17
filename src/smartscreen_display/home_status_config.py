from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_home_status_entities(
    path: str | Path,
) -> list[dict[str, Any]]:
    config_path = Path(path)

    if not config_path.is_file():
        return []

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError):
        return []

    entities = payload.get("entities", [])

    if not isinstance(entities, list):
        return []

    valid_entities = []

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        entity_id = entity.get("entity_id")

        if not isinstance(entity_id, str):
            continue

        if not entity_id:
            continue

        if entity.get("visible") is False:
            continue

        valid_entities.append(entity)

    valid_entities.sort(
        key=lambda entity: (
            entity.get("order")
            if isinstance(entity.get("order"), (int, float))
            else float("inf")
        )
    )

    return valid_entities

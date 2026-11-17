from __future__ import annotations

import json
from pathlib import Path


def load_household_actions(
    path: str | Path,
) -> dict[str, tuple[dict, ...]]:
    config_path = Path(path)

    if not config_path.is_file():
        return {}

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
        return {}

    if not isinstance(payload, dict):
        return {}

    actions = payload.get(
        "actions",
        {},
    )

    if not isinstance(actions, dict):
        return {}

    result = {}

    for action_id, targets in actions.items():
        if (
            not isinstance(action_id, str)
            or not action_id.strip()
            or not isinstance(targets, list)
        ):
            continue

        valid_targets = []

        for target in targets:
            if not isinstance(target, dict):
                continue

            device_id = target.get(
                "device_id"
            )
            control_id = target.get(
                "control_id"
            )

            if (
                not isinstance(device_id, str)
                or not device_id.strip()
                or not isinstance(control_id, str)
                or not control_id.strip()
            ):
                continue

            valid_targets.append(
                {
                    "device_id": device_id,
                    "control_id": control_id,
                    "value": target.get(
                        "value"
                    ),
                }
            )

        result[action_id] = tuple(
            valid_targets
        )

    return result

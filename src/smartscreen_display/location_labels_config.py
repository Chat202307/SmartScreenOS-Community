from __future__ import annotations

import json
from pathlib import Path


def load_location_labels(
    path: str | Path,
) -> dict[str, str]:
    config_path = Path(path)

    if not config_path.is_file():
        return {}

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    rooms = payload.get("rooms", [])

    if not isinstance(rooms, list):
        return {}

    labels = {}

    for room in rooms:
        if not isinstance(room, dict):
            continue

        room_id = room.get("id")
        name = room.get("name")

        if (
            not isinstance(room_id, str)
            or not room_id.strip()
        ):
            continue

        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            continue

        labels[room_id] = name

    return labels



def load_location_orders(
    path: str | Path,
) -> dict[str, float]:
    """Load user-defined room ordering by stable room id."""

    config_path = Path(path)

    if not config_path.is_file():
        return {}

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    rooms = payload.get("rooms", [])

    if not isinstance(rooms, list):
        return {}

    orders = {}

    for room in rooms:
        if not isinstance(room, dict):
            continue

        location_id = room.get("id")
        order = room.get("order")

        if (
            not isinstance(location_id, str)
            or not location_id.strip()
        ):
            continue

        if (
            isinstance(order, bool)
            or not isinstance(
                order,
                (int, float),
            )
        ):
            continue

        orders[location_id] = order

    return orders


def load_location_zones(
    path: str | Path,
) -> dict[str, tuple[str, ...]]:
    config_path = Path(path)

    if not config_path.is_file():
        return {}

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(payload, dict):
        return {}

    zones = payload.get("zones", [])

    if not isinstance(zones, list):
        return {}

    result = {}

    for zone in zones:
        if not isinstance(zone, dict):
            continue

        zone_id = zone.get("id")
        rooms = zone.get("rooms")

        if (
            not isinstance(zone_id, str)
            or not zone_id.strip()
            or not isinstance(rooms, list)
        ):
            continue

        room_ids = tuple(
            room_id
            for room_id in rooms
            if (
                isinstance(room_id, str)
                and room_id.strip()
            )
        )

        result[zone_id] = room_ids

    return result

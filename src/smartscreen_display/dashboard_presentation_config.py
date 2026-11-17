from __future__ import annotations

import json
from pathlib import Path


def load_dashboard_presentation_areas(
    path: str | Path,
) -> dict[str, dict]:
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

    areas = payload.get("areas", [])

    if not isinstance(areas, list):
        return {}

    result = {}

    for area in areas:
        if not isinstance(area, dict):
            continue

        area_id = area.get("id")
        label = area.get("label")
        member_location_ids = area.get(
            "member_location_ids"
        )
        summary_location_id = area.get(
            "summary_location_id"
        )
        order = area.get("order")

        sheet_extra_device_ids = area.get(
            "sheet_extra_device_ids",
            [],
        )
        sheet_device_order = area.get(
            "sheet_device_order",
            [],
        )
        sheet_wide_device_ids = area.get(
            "sheet_wide_device_ids",
            [],
        )

        if (
            not isinstance(area_id, str)
            or not area_id.strip()
            or not isinstance(label, str)
            or not label.strip()
            or not isinstance(
                member_location_ids,
                list,
            )
        ):
            continue

        room_ids = tuple(
            location_id
            for location_id
            in member_location_ids
            if (
                isinstance(location_id, str)
                and location_id.strip()
            )
        )

        if (
            summary_location_id is not None
            and (
                not isinstance(
                    summary_location_id,
                    str,
                )
                or not summary_location_id.strip()
            )
        ):
            summary_location_id = None

        if (
            isinstance(order, bool)
            or not isinstance(
                order,
                (int, float),
            )
        ):
            order = None

        def string_tuple(value):
            if not isinstance(value, list):
                return ()

            result_values = []

            for item in value:
                if (
                    not isinstance(item, str)
                    or not item.strip()
                    or item in result_values
                ):
                    continue

                result_values.append(item)

            return tuple(result_values)

        presentation_area = {
            "label": label,
            "room_ids": room_ids,
            "summary_location_id":
                summary_location_id,
            "order": order,
            "show_on_home": True,
        }

        resolved_sheet_extra_device_ids = (
            string_tuple(
                sheet_extra_device_ids
            )
        )

        if resolved_sheet_extra_device_ids:
            presentation_area[
                "sheet_extra_device_ids"
            ] = (
                resolved_sheet_extra_device_ids
            )

        resolved_sheet_device_order = (
            string_tuple(
                sheet_device_order
            )
        )

        if resolved_sheet_device_order:
            presentation_area[
                "sheet_device_order"
            ] = resolved_sheet_device_order

        resolved_sheet_wide_device_ids = (
            string_tuple(
                sheet_wide_device_ids
            )
        )

        if resolved_sheet_wide_device_ids:
            presentation_area[
                "sheet_wide_device_ids"
            ] = (
                resolved_sheet_wide_device_ids
            )

        result[area_id] = presentation_area

    return result

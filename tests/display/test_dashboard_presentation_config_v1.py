import json

from src.smartscreen_display.dashboard_presentation_config import (
    load_dashboard_presentation_areas,
)


def test_loader_reads_dashboard_presentation_areas(
    tmp_path,
):
    config = tmp_path / "dashboard_presentation.json"

    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "areas": [
                    {
                        "id": "home_kitchen",
                        "label": "厨房",
                        "member_location_ids": [
                            "kitchen",
                        ],
                        "summary_location_id":
                            "open_public_area",
                        "order": 10,
                    },
                    {
                        "id": "home_living_dining",
                        "label": "客餐厅",
                        "member_location_ids": [
                            "living",
                            "dining",
                        ],
                        "summary_location_id":
                            "open_public_area",
                        "order": 20,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert load_dashboard_presentation_areas(
        config
    ) == {
        "home_kitchen": {
            "label": "厨房",
            "room_ids": (
                "kitchen",
            ),
            "summary_location_id":
                "open_public_area",
            "order": 10,
            "show_on_home": True,
        },
        "home_living_dining": {
            "label": "客餐厅",
            "room_ids": (
                "living",
                "dining",
            ),
            "summary_location_id":
                "open_public_area",
            "order": 20,
            "show_on_home": True,
        },
    }


def test_loader_returns_empty_when_file_missing(
    tmp_path,
):
    assert load_dashboard_presentation_areas(
        tmp_path / "missing.json"
    ) == {}


def test_loader_ignores_invalid_area_entries(
    tmp_path,
):
    config = tmp_path / "dashboard_presentation.json"

    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "areas": [
                    {
                        "id": "",
                        "label": "无效",
                        "member_location_ids": [
                            "living",
                        ],
                    },
                    {
                        "id": "valid",
                        "label": "有效",
                        "member_location_ids": [
                            "living",
                            "",
                            123,
                        ],
                        "order": 30,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert load_dashboard_presentation_areas(
        config
    ) == {
        "valid": {
            "label": "有效",
            "room_ids": (
                "living",
            ),
            "summary_location_id": None,
            "order": 30,
            "show_on_home": True,
        },
    }




def test_loader_reads_area_sheet_device_presentation(
    tmp_path,
):
    import json

    config = (
        tmp_path
        / "dashboard_presentation.json"
    )

    config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "areas": [
                    {
                        "id":
                            "home_living_dining",
                        "label": "客餐厅",
                        "member_location_ids": [
                            "living",
                            "dining",
                        ],
                        "sheet_extra_device_ids": [
                            "device.shared",
                            "device.shared",
                            "",
                            123,
                        ],
                        "sheet_device_order": [
                            "device.a",
                            "device.b",
                            "device.a",
                            "",
                            123,
                        ],
                        "sheet_wide_device_ids": [
                            "device.b",
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    area = (
        load_dashboard_presentation_areas(
            config
        )["home_living_dining"]
    )

    assert area["sheet_extra_device_ids"] == (
        "device.shared",
    )

    assert area["sheet_device_order"] == (
        "device.a",
        "device.b",
    )

    assert area["sheet_wide_device_ids"] == (
        "device.b",
    )

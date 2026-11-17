import json

from src.smartscreen_display.location_labels_config import (
    load_location_labels,
)


def test_load_location_labels_reads_user_defined_room_names(
    tmp_path,
):
    path = tmp_path / "home.json"

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rooms": [
                    {
                        "id": "living",
                        "name": "一楼家庭活动区",
                    },
                    {
                        "id": "study",
                        "name": "我的工作间",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    labels = load_location_labels(path)

    assert labels == {
        "living": "一楼家庭活动区",
        "study": "我的工作间",
    }


def test_load_location_labels_returns_empty_for_missing_file(
    tmp_path,
):
    labels = load_location_labels(
        tmp_path / "missing.json"
    )

    assert labels == {}


def test_load_location_labels_returns_empty_for_invalid_json(
    tmp_path,
):
    path = tmp_path / "home.json"
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    assert load_location_labels(path) == {}


def test_load_location_labels_ignores_invalid_rooms(
    tmp_path,
):
    path = tmp_path / "home.json"

    path.write_text(
        json.dumps(
            {
                "rooms": [
                    {
                        "id": "living",
                        "name": "家庭共享区",
                    },
                    {
                        "id": "",
                        "name": "无效",
                    },
                    {
                        "id": "study",
                        "name": "",
                    },
                    {
                        "id": "bedroom",
                    },
                    "invalid",
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert load_location_labels(path) == {
        "living": "家庭共享区",
    }


def test_load_location_labels_preserves_arbitrary_user_name(
    tmp_path,
):
    path = tmp_path / "home.json"

    path.write_text(
        json.dumps(
            {
                "rooms": [
                    {
                        "id": "living",
                        "name": "阳光音乐休息区",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert (
        load_location_labels(path)["living"]
        == "阳光音乐休息区"
    )


def test_load_location_orders_reads_user_defined_room_order(
    tmp_path,
):
    from src.smartscreen_display.location_labels_config import (
        load_location_orders,
    )

    path = tmp_path / "home.json"

    path.write_text(
        json.dumps(
            {
                "rooms": [
                    {
                        "id": "living",
                        "name": "家庭活动室",
                        "order": 30,
                    },
                    {
                        "id": "study",
                        "name": "阅读室",
                        "order": 10,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert load_location_orders(path) == {
        "living": 30,
        "study": 10,
    }


def test_load_location_zones_reads_room_members(
    tmp_path,
):
    from src.smartscreen_display.location_labels_config import (
        load_location_zones,
    )

    path = tmp_path / "home.json"
    path.write_text(
        """
{
  "schema_version": 1,
  "zones": [
    {
      "id": "open_public_area",
      "name": "客餐厨开放区",
      "rooms": [
        "living",
        "dining",
        "kitchen"
      ]
    }
  ]
}
""",
        encoding="utf-8",
    )

    assert load_location_zones(path) == {
        "open_public_area": (
            "living",
            "dining",
            "kitchen",
        ),
    }


def test_load_location_zones_ignores_invalid_entries(
    tmp_path,
):
    from src.smartscreen_display.location_labels_config import (
        load_location_zones,
    )

    path = tmp_path / "home.json"
    path.write_text(
        """
{
  "zones": [
    null,
    {},
    {
      "id": "",
      "rooms": ["living"]
    },
    {
      "id": "valid",
      "rooms": [
        "living",
        "",
        123,
        "dining"
      ]
    }
  ]
}
""",
        encoding="utf-8",
    )

    assert load_location_zones(path) == {
        "valid": (
            "living",
            "dining",
        ),
    }

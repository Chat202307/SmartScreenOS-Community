import json

from src.smartscreen_display.home_status_config import (
    load_home_status_entities,
)


def test_load_home_status_entities(tmp_path):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "binary_sensor.front_door",
                        "name": "入户门",
                    },
                    {
                        "entity_id": "light.living_room",
                        "name": "客厅主灯",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert load_home_status_entities(path) == [
        {
            "entity_id": "binary_sensor.front_door",
            "name": "入户门",
        },
        {
            "entity_id": "light.living_room",
            "name": "客厅主灯",
        },
    ]


def test_missing_home_status_config_returns_empty(tmp_path):
    path = tmp_path / "missing.json"

    assert load_home_status_entities(path) == []


def test_invalid_json_returns_empty(tmp_path):
    path = tmp_path / "home_entities.json"
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    assert load_home_status_entities(path) == []


def test_invalid_entities_type_returns_empty(tmp_path):
    path = tmp_path / "home_entities.json"
    path.write_text(
        '{"entities":"invalid"}',
        encoding="utf-8",
    )

    assert load_home_status_entities(path) == []


def test_invalid_entity_entries_are_ignored(tmp_path):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.living_room",
                        "name": "客厅灯",
                    },
                    {
                        "name": "没有 entity id",
                    },
                    "invalid",
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    assert load_home_status_entities(path) == [
        {
            "entity_id": "light.living_room",
            "name": "客厅灯",
        }
    ]


def test_home_status_entities_are_sorted_by_order(tmp_path):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.third",
                        "name": "第三",
                        "order": 30,
                    },
                    {
                        "entity_id": "light.first",
                        "name": "第一",
                        "order": 10,
                    },
                    {
                        "entity_id": "light.second",
                        "name": "第二",
                        "order": 20,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entities = load_home_status_entities(path)

    assert [
        entity["entity_id"]
        for entity in entities
    ] == [
        "light.first",
        "light.second",
        "light.third",
    ]


def test_home_status_entities_without_order_sort_last(tmp_path):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.no_order",
                        "name": "未排序",
                    },
                    {
                        "entity_id": "light.ordered",
                        "name": "已排序",
                        "order": 10,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entities = load_home_status_entities(path)

    assert [
        entity["entity_id"]
        for entity in entities
    ] == [
        "light.ordered",
        "light.no_order",
    ]


def test_home_status_entities_hide_explicitly_invisible_items(tmp_path):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.visible",
                        "name": "显示设备",
                        "order": 10,
                    },
                    {
                        "entity_id": "light.hidden",
                        "name": "隐藏设备",
                        "order": 20,
                        "visible": False,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entities = load_home_status_entities(path)

    assert [
        entity["entity_id"]
        for entity in entities
    ] == [
        "light.visible",
    ]


def test_home_status_entity_is_visible_by_default(tmp_path):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.default",
                        "name": "默认显示设备",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entities = load_home_status_entities(path)

    assert [
        entity["entity_id"]
        for entity in entities
    ] == [
        "light.default",
    ]


def test_home_status_entities_preserve_action_metadata(
    tmp_path,
):
    path = tmp_path / "home_entities.json"

    path.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.living_room",
                        "name": "客厅主灯",
                        "order": 10,
                        "action": "toggle",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entities = load_home_status_entities(path)

    assert entities == [
        {
            "entity_id": "light.living_room",
            "name": "客厅主灯",
            "order": 10,
            "action": "toggle",
        }
    ]

import json
from pathlib import Path


CONFIG_PATH = Path("config/home_entities.json")


def load_config():
    return json.loads(
        CONFIG_PATH.read_text(
            encoding="utf-8"
        )
    )


def test_home_entities_config_exists():
    assert CONFIG_PATH.is_file()


def test_home_entities_config_is_valid_json():
    payload = load_config()

    assert isinstance(payload, dict)


def test_home_entities_config_has_entities():
    payload = load_config()

    assert isinstance(
        payload.get("entities"),
        list,
    )


def test_home_entities_have_entity_ids():
    payload = load_config()

    for entity in payload["entities"]:
        assert isinstance(entity, dict)
        assert isinstance(
            entity.get("entity_id"),
            str,
        )
        assert entity["entity_id"]


def test_home_entities_have_display_names():
    payload = load_config()

    for entity in payload["entities"]:
        assert isinstance(
            entity.get("name"),
            str,
        )
        assert entity["name"]

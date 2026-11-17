import json

import pytest


def test_load_calendar_config(tmp_path):
    from src.smartscreen_display.calendar_config import (
        load_calendar_config,
    )

    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": True,
                "provider": "eventkit",
                "calendar_id": (
                    "DA75048B-8C73-4D7D-9D54-"
                    "7FE22216A1BA"
                ),
                "bridge_executable": (
                    "var/eventkit_calendar_bridge"
                ),
            }
        ),
        encoding="utf-8",
    )

    config = load_calendar_config(path)

    assert config.enabled is True
    assert config.provider == "eventkit"
    assert config.calendar_id == (
        "DA75048B-8C73-4D7D-9D54-"
        "7FE22216A1BA"
    )
    assert config.bridge_executable == (
        "var/eventkit_calendar_bridge"
    )


def test_calendar_config_rejects_blank_calendar_id(
    tmp_path,
):
    from src.smartscreen_display.calendar_config import (
        load_calendar_config,
    )

    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": True,
                "provider": "eventkit",
                "calendar_id": " ",
                "bridge_executable": (
                    "var/eventkit_calendar_bridge"
                ),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_calendar_config(path)


def test_calendar_config_rejects_unknown_provider(
    tmp_path,
):
    from src.smartscreen_display.calendar_config import (
        load_calendar_config,
    )

    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": True,
                "provider": "unknown",
                "calendar_id": "family-calendar",
                "bridge_executable": (
                    "var/eventkit_calendar_bridge"
                ),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_calendar_config(path)


def test_disabled_calendar_does_not_require_identity(
    tmp_path,
):
    from src.smartscreen_display.calendar_config import (
        load_calendar_config,
    )

    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": False,
            }
        ),
        encoding="utf-8",
    )

    config = load_calendar_config(path)

    assert config.enabled is False
    assert config.provider is None
    assert config.calendar_id is None
    assert config.bridge_executable is None


def test_calendar_config_allows_all_calendars(
    tmp_path,
):
    from src.smartscreen_display.calendar_config import (
        load_calendar_config,
    )

    path = tmp_path / "calendar.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "enabled": True,
                "provider": "eventkit",
                "bridge_executable": (
                    "var/eventkit_calendar_bridge"
                ),
            }
        ),
        encoding="utf-8",
    )

    config = load_calendar_config(path)

    assert config.enabled is True
    assert config.provider == "eventkit"
    assert config.calendar_id is None
    assert config.bridge_executable == (
        "var/eventkit_calendar_bridge"
    )

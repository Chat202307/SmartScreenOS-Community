from __future__ import annotations

import os
from typing import Any

from .home_assistant_client import HomeAssistantClient
from .home_status import HomeAssistantHomeStatusProvider
from .home_status_config import load_home_status_entities


DEFAULT_ENTITIES = [
    {
        "entity_id": "binary_sensor.demo_entity_001",
        "name": "门窗",
        "states": {
            "on": "已打开",
            "off": "已关闭",
        },
    },
    {
        "entity_id": "binary_sensor.demo_entity_010",
        "name": "人体感应",
        "states": {
            "on": "有人",
            "off": "无人",
        },
    },
    {
        "entity_id": "light.demo_entity_024",
        "name": "客厅主灯",
        "states": {
            "on": "开启",
            "off": "关闭",
        },
    },
]


def create_home_assistant_provider(
    *,
    client=None,
    base_url: str | None = None,
    token: str | None = None,
    entities: list[dict[str, Any]] | None = None,
    entities_file: str | os.PathLike[str] | None = None,
    change_notifier=None,
):
    resolved_client = client

    if resolved_client is None:
        resolved_url = (
            base_url
            or os.environ.get("SMARTSCREEN_HA_URL")
        )

        resolved_token = (
            token
            or os.environ.get("SMARTSCREEN_HA_TOKEN")
        )

        if not resolved_url or not resolved_token:
            return None

        resolved_client = HomeAssistantClient(
            resolved_url,
            resolved_token,
        )

    resolved_entities = entities

    if (
        resolved_entities is None
        and entities_file is not None
    ):
        loaded_entities = load_home_status_entities(
            entities_file
        )

        if loaded_entities:
            resolved_entities = loaded_entities

    if resolved_entities is None:
        resolved_entities = DEFAULT_ENTITIES

    return HomeAssistantHomeStatusProvider(
        resolved_client,
        entities=resolved_entities,
        change_notifier=change_notifier,
    )

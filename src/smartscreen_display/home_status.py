from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileHomeStatusProvider:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def get_items(self) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []

        try:
            payload = json.loads(
                self._path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return []

        items = payload.get("items", [])

        if not isinstance(items, list):
            return []

        return items


class HomeAssistantHomeStatusProvider:
    def __init__(
        self,
        client,
        *,
        entities: list[dict[str, Any]],
        change_notifier=None,
    ) -> None:
        self._client = client
        self._entities = entities
        self._state_cache = []
        self._revision = 0
        self._available = False
        self._change_notifier = change_notifier

    @property
    def revision(self) -> int:
        return self._revision

    @property
    def available(self) -> bool:
        return self._available

    def refresh(self) -> None:
        try:
            states = self._client.get_json(
                "/api/states"
            )
        except OSError:
            self._available = False
            return

        if not isinstance(states, list):
            self._available = False
            return

        self._state_cache = states
        self._available = True

    def update_state(
        self,
        entity_id: str,
        new_state: dict[str, Any] | None,
    ) -> None:
        if (
            new_state is not None
            and new_state.get("entity_id")
            != entity_id
        ):
            raise ValueError(
                "state entity_id mismatch"
            )

        updated_states = []

        for state in self._state_cache:
            if not isinstance(state, dict):
                updated_states.append(state)
                continue

            if state.get("entity_id") == entity_id:
                continue

            updated_states.append(state)

        if new_state is not None:
            updated_states.append(
                new_state
            )

        if updated_states != self._state_cache:
            self._state_cache = updated_states
            self._revision += 1

            if self._change_notifier is not None:
                self._change_notifier.notify(
                    self._revision
                )

    def get_cached_items(
        self,
    ) -> list[dict[str, Any]]:
        return self._items_from_states(
            self._state_cache
        )

    def perform_cover_action(
        self,
        entity_id: str,
        action: str,
    ) -> Any:
        configured_entity = None

        for config in self._entities:
            if config.get("entity_id") == entity_id:
                configured_entity = config
                break

        if (
            configured_entity is None
            or configured_entity.get(
                "cover_control"
            ) is not True
        ):
            raise ValueError(
                "cover control not allowed"
            )

        services = {
            "open": "open_cover",
            "stop": "stop_cover",
            "close": "close_cover",
        }

        service = services.get(action)

        if service is None:
            raise ValueError(
                "cover action not supported"
            )

        return self._client.call_service(
            "cover",
            service,
            entity_id,
        )

    def set_hvac_mode(
        self,
        entity_id: str,
        hvac_mode: str,
    ) -> Any:
        configured_entity = None

        for config in self._entities:
            if config.get("entity_id") == entity_id:
                configured_entity = config
                break

        if (
            configured_entity is None
            or configured_entity.get(
                "hvac_mode_control"
            ) is not True
        ):
            raise ValueError(
                "hvac mode control not allowed"
            )

        state = self._client.get_json(
            "/api/states/" + entity_id
        )

        if not isinstance(state, dict):
            raise ValueError(
                "hvac modes unavailable"
            )

        attributes = state.get(
            "attributes",
            {},
        )

        if not isinstance(attributes, dict):
            raise ValueError(
                "hvac modes unavailable"
            )

        hvac_modes = attributes.get(
            "hvac_modes"
        )

        if not isinstance(hvac_modes, list):
            raise ValueError(
                "hvac modes unavailable"
            )

        if hvac_mode not in hvac_modes:
            raise ValueError(
                "hvac mode not supported"
            )

        return self._client.call_service(
            "climate",
            "set_hvac_mode",
            entity_id,
            service_data={
                "hvac_mode": hvac_mode,
            },
        )

    def set_fan_mode(
        self,
        entity_id: str,
        fan_mode: str,
    ) -> Any:
        configured_entity = None

        for config in self._entities:
            if config.get("entity_id") == entity_id:
                configured_entity = config
                break

        if (
            configured_entity is None
            or configured_entity.get(
                "fan_control"
            ) is not True
        ):
            raise ValueError(
                "fan control not allowed"
            )

        state = self._client.get_json(
            "/api/states/" + entity_id
        )

        if not isinstance(state, dict):
            raise ValueError(
                "fan modes unavailable"
            )

        attributes = state.get(
            "attributes",
            {},
        )

        if not isinstance(attributes, dict):
            raise ValueError(
                "fan modes unavailable"
            )

        fan_modes = attributes.get(
            "fan_modes"
        )

        if not isinstance(fan_modes, list):
            raise ValueError(
                "fan modes unavailable"
            )

        if fan_mode not in fan_modes:
            raise ValueError(
                "fan mode not supported"
            )

        return self._client.call_service(
            "climate",
            "set_fan_mode",
            entity_id,
            service_data={
                "fan_mode": fan_mode,
            },
        )

    def set_temperature(
        self,
        entity_id: str,
        temperature: float,
        *,
        min_temp: float | None = None,
        max_temp: float | None = None,
        step: float | None = None,
    ) -> Any:
        configured_entity = None

        for config in self._entities:
            if config.get("entity_id") == entity_id:
                configured_entity = config
                break

        if (
            configured_entity is None
            or configured_entity.get(
                "temperature_control"
            ) is not True
        ):
            raise ValueError(
                "temperature control not allowed"
            )

        if (
            min_temp is None
            or max_temp is None
            or step is None
        ):
            state = self._client.get_json(
                "/api/states/" + entity_id
            )

            if not isinstance(state, dict):
                raise ValueError(
                    "temperature limits unavailable"
                )

            attributes = state.get(
                "attributes",
                {},
            )

            if not isinstance(attributes, dict):
                raise ValueError(
                    "temperature limits unavailable"
                )

            min_temp = attributes.get(
                "min_temp"
            )
            max_temp = attributes.get(
                "max_temp"
            )
            step = attributes.get(
                "target_temp_step"
            )

        if not isinstance(
            min_temp,
            (int, float),
        ) or not isinstance(
            max_temp,
            (int, float),
        ) or not isinstance(
            step,
            (int, float),
        ):
            raise ValueError(
                "temperature limits unavailable"
            )

        if (
            temperature < min_temp
            or temperature > max_temp
        ):
            raise ValueError(
                "temperature out of range"
            )

        if step <= 0:
            raise ValueError(
                "invalid temperature step"
            )

        steps = (
            temperature - min_temp
        ) / step

        if abs(
            steps - round(steps)
        ) > 1e-9:
            raise ValueError(
                "invalid temperature step"
            )

        return self._client.call_service(
            "climate",
            "set_temperature",
            entity_id,
            service_data={
                "temperature": temperature,
            },
        )

    def perform_action(
        self,
        entity_id: str,
        action: str,
    ) -> Any:
        for config in self._entities:
            configured_entity_id = config.get(
                "entity_id"
            )

            if configured_entity_id != entity_id:
                continue

            configured_action = config.get(
                "action"
            )
            configured_actions = config.get(
                "actions"
            )

            action_allowed = (
                configured_action == action
                or (
                    isinstance(
                        configured_actions,
                        list,
                    )
                    and action in configured_actions
                )
            )

            if not action_allowed:
                raise ValueError(
                    "action not allowed"
                )

            if "." not in entity_id:
                raise ValueError(
                    "action not allowed"
                )

            domain = entity_id.split(
                ".",
                1,
            )[0]

            return self._client.call_service(
                domain,
                action,
                entity_id,
            )

        raise ValueError(
            "action not allowed"
        )

    def _default_state_map(
        self,
        entity_id: str,
        attributes: dict[str, Any],
    ) -> dict[str, str]:
        if entity_id.startswith("light."):
            return {
                "on": "开启",
                "off": "关闭",
            }

        if entity_id.startswith("cover."):
            return {
                "open": "已打开",
                "closed": "已关闭",
                "opening": "正在打开",
                "closing": "正在关闭",
            }

        if entity_id.startswith("climate."):
            return {
                "off": "关闭",
                "cool": "制冷",
                "heat": "制热",
                "auto": "自动",
                "dry": "除湿",
                "fan_only": "送风",
            }

        if entity_id.startswith("binary_sensor."):
            device_class = attributes.get("device_class")

            if device_class in {
                "door",
                "garage_door",
                "opening",
                "window",
            }:
                return {
                    "on": "已打开",
                    "off": "已关闭",
                }

            if device_class in {
                "motion",
                "occupancy",
                "presence",
            }:
                return {
                    "on": "有人",
                    "off": "无人",
                }

        return {}

    def get_items(self) -> list[dict[str, Any]]:
        self.refresh()

        return self.get_cached_items()

    def _items_from_states(
        self,
        states: list[Any],
    ) -> list[dict[str, Any]]:
        state_by_entity = {}

        for state in states:
            if not isinstance(state, dict):
                continue

            entity_id = state.get("entity_id")

            if not isinstance(entity_id, str):
                continue

            state_by_entity[entity_id] = state

        items = []

        for config in self._entities:
            entity_id = config.get("entity_id")

            if not isinstance(entity_id, str):
                continue

            state = state_by_entity.get(entity_id)

            if state is None:
                continue

            raw_state = state.get("state", "")
            attributes = state.get("attributes", {})

            if not isinstance(attributes, dict):
                attributes = {}

            friendly_name = config.get(
                "name"
            ) or attributes.get(
                "friendly_name",
                entity_id,
            )

            state_map = config.get("states", {})

            if not isinstance(state_map, dict):
                state_map = {}

            semantic_state_map = self._default_state_map(
                entity_id,
                attributes,
            )

            fallback_state_map = {
                "unknown": "未知",
                "unavailable": "离线",
            }

            display_state = state_map.get(
                raw_state,
                semantic_state_map.get(
                    raw_state,
                    fallback_state_map.get(
                        raw_state,
                        raw_state,
                    ),
                ),
            )

            item = {
                "name": friendly_name,
                "state": display_state,
            }

            icon = config.get("icon")

            if isinstance(icon, str) and icon:
                item["icon"] = icon

            action = config.get("action")
            actions = config.get("actions")

            if isinstance(action, str) and action:
                item["action"] = action
                item["entity_id"] = entity_id
                item["raw_state"] = raw_state

            if (
                isinstance(actions, list)
                and actions
            ):
                item["actions"] = actions
                item["entity_id"] = entity_id
                item["raw_state"] = raw_state

            if (
                config.get("cover_control") is True
                and entity_id.startswith("cover.")
            ):
                item["cover_control"] = True
                item["entity_id"] = entity_id
                item["raw_state"] = raw_state

                position = attributes.get(
                    "current_position"
                )

                if (
                    isinstance(position, (int, float))
                    and not isinstance(position, bool)
                    and 0 <= position <= 100
                ):
                    item["position"] = position

            if entity_id.startswith("climate."):
                climate_fields = (
                    "current_temperature",
                    "temperature",
                    "fan_mode",
                    "min_temp",
                    "max_temp",
                    "target_temp_step",
                )

                for field in climate_fields:
                    value = attributes.get(field)

                    if value is not None:
                        item[field] = value

            items.append(item)

        return items

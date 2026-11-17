from __future__ import annotations

from typing import Any

from src.smartscreen_platform.contracts import Observation


class HomeAssistantObservationAdapter:
    """Convert configured Home Assistant states into platform observations."""

    def __init__(
        self,
        *,
        entities: list[dict[str, Any]],
    ) -> None:
        self._entities = {
            entity["entity_id"]: dict(entity)
            for entity in entities
            if isinstance(entity, dict)
            and isinstance(entity.get("entity_id"), str)
            and entity["entity_id"]
        }

    def convert(
        self,
        state: dict[str, Any],
    ) -> list[Observation]:
        entity_id = state.get("entity_id")

        if not isinstance(entity_id, str):
            return []

        config = self._entities.get(entity_id)

        if config is None:
            return []

        raw_value = state.get("state")

        if raw_value in {
            None,
            "unknown",
            "unavailable",
        }:
            return []

        parameter = config.get("parameter")

        if (
            not isinstance(parameter, str)
            or not parameter
        ):
            return []

        value_type = config.get(
            "value_type",
            "string",
        )

        try:
            value = self._convert_value(
                raw_value,
                value_type,
            )
        except (TypeError, ValueError):
            return []

        attributes = state.get(
            "attributes",
            {},
        )

        if not isinstance(attributes, dict):
            attributes = {}

        unit = config.get("unit")

        if unit is None:
            unit = attributes.get(
                "unit_of_measurement"
            )

        return [
            Observation.create(
                parameter=parameter,
                value=value,
                unit=unit,
                confidence=1.0,
                location_id=config.get(
                    "location_id"
                ),
                provenance={
                    "provider": "home_assistant",
                    "entity_id": entity_id,
                },
            )
        ]

    @staticmethod
    def _convert_value(
        value: Any,
        value_type: str,
    ) -> Any:
        if value_type == "float":
            return float(value)

        if value_type == "int":
            return int(value)

        if value_type == "bool":
            if value in {
                True,
                "on",
                "true",
                "1",
                1,
            }:
                return True

            if value in {
                False,
                "off",
                "false",
                "0",
                0,
            }:
                return False

            raise ValueError(
                "invalid boolean value"
            )

        if value_type == "string":
            return str(value)

        raise ValueError(
            "unsupported value type"
        )

from __future__ import annotations

from typing import Any

from src.smartscreen_platform.device_data import (
    DeviceDataIngestionService,
    DeviceRegistry,
)


class HomeAssistantDeviceDataAdapter:
    ADAPTER_ID = "home_assistant"

    def __init__(
        self,
        *,
        registry: DeviceRegistry,
        ingestion: DeviceDataIngestionService,
    ):
        self._registry = registry
        self._ingestion = ingestion
        self._devices_by_entity_id = {}

        for device in registry.all():
            if (
                device.adapter_id
                != self.ADAPTER_ID
            ):
                continue

            adapter_config = (
                device.adapter_config
                if isinstance(
                    device.adapter_config,
                    dict,
                )
                else {}
            )

            entity_id = adapter_config.get(
                "entity_id"
            )

            if (
                isinstance(entity_id, str)
                and entity_id.strip()
            ):
                self._devices_by_entity_id[
                    entity_id.strip()
                ] = device

    def ingest_state(
        self,
        *,
        entity_id: str,
        raw_state: Any,
    ):
        source_unit = None

        if isinstance(raw_state, dict):
            attributes = raw_state.get(
                "attributes",
                {},
            )

            if isinstance(
                attributes,
                dict,
            ):
                source_unit = (
                    attributes.get(
                        "unit_of_measurement"
                    )
                )

            device = (
                self._devices_by_entity_id.get(
                    entity_id
                )
            )

            if device is not None:
                return self._ingest_entity_state(
                    device=device,
                    entity_id=entity_id,
                    state=raw_state,
                )

            raw_state = raw_state.get(
                "state"
            )

        binding = self._registry.resolve_source(
            adapter_id=self.ADAPTER_ID,
            source_id=entity_id,
        )

        if binding is None:
            return None

        available = raw_state not in {
            None,
            "unknown",
            "unavailable",
        }

        if available:
            value = self._convert_value(
                raw_state,
                binding.value_type,
            )

            value = (
                self._canonical_scalar_value(
                    parameter=(
                        binding.parameter
                    ),
                    value=value,
                    source_unit=source_unit,
                    target_unit=binding.unit,
                )
            )
        else:
            value = raw_state

        return self._ingestion.ingest(
            adapter_id=self.ADAPTER_ID,
            source_id=entity_id,
            value=value,
            available=available,
        )

    def _ingest_entity_state(
        self,
        *,
        device,
        entity_id,
        state,
    ):
        entity_state = state.get("state")

        entity_available = (
            entity_state
            not in {
                None,
                "unknown",
                "unavailable",
            }
        )

        attributes = state.get(
            "attributes",
            {},
        )

        if not isinstance(
            attributes,
            dict,
        ):
            attributes = {}

        if entity_id.startswith(
            "climate."
        ):
            raw_values = {
                "operating_state": (
                    entity_state
                    if entity_available
                    else None
                ),
                "target_temperature": (
                    attributes.get(
                        "temperature"
                    )
                    if entity_available
                    else None
                ),
                "current_temperature": (
                    attributes.get(
                        "current_temperature"
                    )
                    if entity_available
                    else None
                ),
                "fan_mode": (
                    attributes.get(
                        "fan_mode"
                    )
                    if entity_available
                    else None
                ),
            }
        elif entity_id.startswith(
            "cover."
        ):
            raw_values = {
                "state": (
                    entity_state
                    if entity_available
                    else None
                ),
                "position": (
                    attributes.get(
                        "current_position"
                    )
                    if entity_available
                    else None
                ),
            }
        else:
            raw_values = {
                "power": (
                    entity_state
                    if entity_available
                    else None
                ),
                "brightness": (
                    attributes.get(
                        "brightness"
                    )
                    if entity_available
                    else None
                ),
                "color_temperature": (
                    attributes.get(
                        "color_temp_kelvin"
                    )
                    if entity_available
                    else None
                ),
            }

        observations = []

        for (
            parameter,
            raw_value,
        ) in raw_values.items():
            definition = (
                device.parameters.get(
                    parameter
                )
            )

            if definition is None:
                continue

            available = (
                entity_available
                and raw_value is not None
            )

            if available:
                value = (
                    self._canonical_value(
                        parameter=parameter,
                        raw_value=raw_value,
                        value_type=(
                            definition.value_type
                        ),
                    )
                )
            else:
                value = raw_value

            observations.append(
                self._ingestion.ingest(
                    adapter_id=self.ADAPTER_ID,
                    source_id=(
                        definition.source_id
                    ),
                    value=value,
                    available=available,
                )
            )

        return observations

    def _canonical_value(
        self,
        *,
        parameter,
        raw_value,
        value_type,
    ):
        if parameter == "brightness":
            brightness = int(raw_value)

            if (
                brightness < 0
                or brightness > 255
            ):
                raise ValueError(
                    "invalid home assistant "
                    "brightness"
                )

            return round(
                brightness * 100 / 255
            )

        if parameter == "position":
            position = int(raw_value)

            if (
                position < 0
                or position > 100
            ):
                raise ValueError(
                    "invalid home assistant "
                    "cover position"
                )

            return position

        return self._convert_value(
            raw_value,
            value_type,
        )

    @staticmethod
    def _canonical_scalar_value(
        *,
        parameter,
        value,
        source_unit,
        target_unit,
    ):
        if (
            parameter == "temperature"
            and source_unit == "°F"
            and target_unit == "°C"
        ):
            return (
                float(value) - 32.0
            ) * 5.0 / 9.0

        return value

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

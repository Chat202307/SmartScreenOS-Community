from __future__ import annotations

import json


class DnakeMqttDeviceDataAdapter:
    ADAPTER_ID = "dnake_mqtt"

    CURTAIN_STATE_VALUES = {
        "OPEN": "open",
        "CLOSE": "closed",
        "STOPPED": "stopped",
    }

    POWER_STATE_VALUES = {
        "ON": True,
        "OFF": False,
    }

    def __init__(
        self,
        *,
        registry,
        ingestion,
    ):
        self._registry = registry
        self._ingestion = ingestion

        self._air_devices_by_state_topic = {}

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

            state_topic = (
                adapter_config.get(
                    "state_topic"
                )
            )

            if (
                isinstance(
                    state_topic,
                    str,
                )
                and state_topic.strip()
            ):
                self._air_devices_by_state_topic[
                    state_topic.strip()
                ] = device

    def _direct_value(
        self,
        *,
        binding,
        raw_payload,
    ):
        raw_value = (
            raw_payload.decode("utf-8")
            if isinstance(
                raw_payload,
                bytes,
            )
            else str(raw_payload)
        ).strip()

        if binding.parameter == "state":
            try:
                return self.CURTAIN_STATE_VALUES[
                    raw_value.upper()
                ]
            except KeyError as exc:
                raise ValueError(
                    "unsupported dnake "
                    "curtain state: "
                    + raw_value
                ) from exc

        if binding.parameter == "power":
            try:
                return self.POWER_STATE_VALUES[
                    raw_value.upper()
                ]
            except KeyError as exc:
                raise ValueError(
                    "unsupported dnake "
                    "power state: "
                    + raw_value
                ) from exc

        return raw_value

    def ingest_message(
        self,
        *,
        topic,
        raw_payload,
    ):
        air_device = (
            self._air_devices_by_state_topic.get(
                topic
            )
        )

        if air_device is not None:
            return (
                self._ingest_air_state(
                    device=air_device,
                    raw_payload=raw_payload,
                )
            )

        binding = self._registry.resolve_source(
            adapter_id=self.ADAPTER_ID,
            source_id=topic,
        )

        if binding is None:
            return None

        value = self._direct_value(
            binding=binding,
            raw_payload=raw_payload,
        )

        return self._ingestion.ingest(
            adapter_id=self.ADAPTER_ID,
            source_id=topic,
            value=value,
            available=True,
        )

    def restore_message(
        self,
        *,
        topic,
        raw_payload,
    ):
        binding = self._registry.resolve_source(
            adapter_id=self.ADAPTER_ID,
            source_id=topic,
        )

        if binding is None:
            return None

        value = self._direct_value(
            binding=binding,
            raw_payload=raw_payload,
        )

        return self._ingestion.restore(
            adapter_id=self.ADAPTER_ID,
            source_id=topic,
            value=value,
            available=True,
        )

    def _ingest_air_state(
        self,
        *,
        device,
        raw_payload,
    ):
        raw_value = (
            raw_payload.decode("utf-8")
            if isinstance(
                raw_payload,
                bytes,
            )
            else str(raw_payload)
        ).strip()

        try:
            payload = json.loads(
                raw_value
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid dnake air state"
            ) from exc

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "invalid dnake air state"
            )

        power = str(
            payload.get(
                "power",
                "UNKNOWN",
            )
        ).upper()

        mode = str(
            payload.get(
                "mode",
                "UNKNOWN",
            )
        ).upper()

        if power == "OFF":
            operating_state = "off"
        elif mode == "COOL":
            operating_state = "cool"
        elif mode == "HEAT":
            operating_state = "heat"
        else:
            operating_state = "unknown"

        canonical_values = {
            "operating_state": (
                operating_state
            ),
            "target_temperature": (
                self._float_value(
                    payload.get(
                        "temp_set"
                    )
                )
            ),
            "current_temperature": (
                self._float_value(
                    payload.get(
                        "temp_room"
                    )
                )
            ),
            "fan_mode": (
                None
                if str(
                    payload.get(
                        "fan",
                        "UNKNOWN",
                    )
                ).upper()
                == "UNKNOWN"
                else str(
                    payload.get(
                        "fan"
                    )
                ).lower()
            ),
        }

        observations = []

        for (
            parameter,
            value,
        ) in canonical_values.items():
            definition = (
                device.parameters.get(
                    parameter
                )
            )

            if definition is None:
                continue

            observations.append(
                self._ingestion.ingest(
                    adapter_id=(
                        self.ADAPTER_ID
                    ),
                    source_id=(
                        definition.source_id
                    ),
                    value=value,
                    available=(
                        value is not None
                    ),
                )
            )

        return observations

    @staticmethod
    def _float_value(value):
        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "invalid dnake air "
                "temperature"
            )

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "invalid dnake air "
                "temperature"
            ) from exc

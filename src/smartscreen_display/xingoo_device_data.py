from __future__ import annotations


class XingooDeviceDataAdapter:
    ADAPTER_ID = "xingoo"

    def __init__(
        self,
        *,
        registry,
        ingestion,
    ):
        self._registry = registry
        self._ingestion = ingestion

    @staticmethod
    def make_source_id(
        iot_id,
        property_name,
    ):
        return (
            str(iot_id)
            + ":"
            + str(property_name)
        )

    def ingest_properties(
        self,
        *,
        iot_id,
        properties,
    ):
        if not isinstance(
            properties,
            dict,
        ):
            raise TypeError(
                "properties must be a dict"
            )

        observations = []

        for (
            property_name,
            raw_value,
        ) in properties.items():
            source_id = self.make_source_id(
                iot_id,
                property_name,
            )

            binding = (
                self._registry.resolve_source(
                    adapter_id=(
                        self.ADAPTER_ID
                    ),
                    source_id=source_id,
                )
            )

            if binding is None:
                continue

            available = (
                raw_value
                not in {
                    None,
                    "unavailable",
                    "unknown",
                }
            )

            if available:
                value = self._convert_value(
                    raw_value,
                    binding.value_type,
                )

                if (
                    property_name
                    == "ScreenSwitch"
                    and binding.parameter
                    == "screen_on"
                ):
                    value = not value

            else:
                value = raw_value

            observation = (
                self._ingestion.ingest(
                    adapter_id=(
                        self.ADAPTER_ID
                    ),
                    source_id=source_id,
                    value=value,
                    available=available,
                )
            )

            observations.append(
                observation
            )

        return observations

    @staticmethod
    def _convert_value(
        raw_value,
        value_type,
    ):
        if value_type == "float":
            return float(
                raw_value
            )

        if value_type == "int":
            return int(
                raw_value
            )

        if value_type == "bool":
            if raw_value in {
                True,
                "on",
                "true",
                "1",
                1,
            }:
                return True

            if raw_value in {
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

        return str(
            raw_value
        )

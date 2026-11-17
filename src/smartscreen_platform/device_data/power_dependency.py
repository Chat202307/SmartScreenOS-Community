from __future__ import annotations


class DevicePowerDependencyResolver:
    def __init__(
        self,
        *,
        registry,
        store,
    ):
        self._registry = registry
        self._store = store

    def resolve(
        self,
        *,
        device_id,
        parameter,
    ) -> str:
        entry = self._store.get(
            device_id,
            parameter,
        )

        device = self._registry.get(
            device_id
        )

        if device is None:
            return "unavailable"

        power_source_device_id = (
            device.power_source_device_id
        )

        if power_source_device_id:
            power_source_entry = (
                self._store.get(
                    power_source_device_id,
                    "power",
                )
            )

            if (
                power_source_entry is not None
                and power_source_entry.available
                and power_source_entry.value is False
            ):
                return "powered_off_by_upstream"

        if entry is None:
            return "unavailable"

        if entry.available:
            return "available"

        return "unavailable"

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .registry import DeviceRegistry


class DeviceParameterStoreError(ValueError):
    pass


@dataclass(frozen=True)
class DeviceParameterValue:
    device_id: str
    location_id: str
    parameter: str
    value: Any
    unit: Optional[str] = None
    available: bool = True
    updated_at: str = ""


class DeviceParameterStore:
    def __init__(
        self,
        *,
        registry: DeviceRegistry,
        clock=None,
    ):
        self._registry = registry
        self._clock = (
            clock
            if clock is not None
            else lambda: datetime.now(timezone.utc)
        )
        self._lock = threading.RLock()
        self._values = {}

    def _store_value(
        self,
        *,
        device_id,
        parameter,
        value,
        available,
        updated_at,
    ):
        device = self._registry.get(
            device_id
        )

        if device is None:
            raise DeviceParameterStoreError(
                "unknown device_id: "
                + str(device_id)
            )

        definition = device.parameters.get(
            parameter
        )

        if definition is None:
            raise DeviceParameterStoreError(
                "unknown parameter for device "
                + str(device_id)
                + ": "
                + str(parameter)
            )

        binding = self._registry.resolve_parameter(
            device_id=device.device_id,
            parameter=definition.parameter,
        )

        if binding is None:
            raise DeviceParameterStoreError(
                "missing parameter binding for device "
                + str(device_id)
                + ": "
                + str(parameter)
            )

        entry = DeviceParameterValue(
            device_id=device.device_id,
            location_id=binding.location_id,
            parameter=definition.parameter,
            value=value,
            unit=definition.unit,
            available=bool(available),
            updated_at=updated_at,
        )

        with self._lock:
            self._values[
                (
                    device.device_id,
                    definition.parameter,
                )
            ] = entry

        return entry

    def update(
        self,
        *,
        device_id,
        parameter,
        value,
        available=True,
    ):
        updated_at = (
            self._clock()
            .astimezone(timezone.utc)
            .isoformat()
        )

        return self._store_value(
            device_id=device_id,
            parameter=parameter,
            value=value,
            available=available,
            updated_at=updated_at,
        )

    def restore(
        self,
        *,
        device_id,
        parameter,
        value,
        available=True,
    ):
        return self._store_value(
            device_id=device_id,
            parameter=parameter,
            value=value,
            available=available,
            updated_at="",
        )

    def restore_source(
        self,
        *,
        adapter_id,
        source_id,
        value,
        available=True,
    ):
        binding = self._registry.resolve_source(
            adapter_id=adapter_id,
            source_id=source_id,
        )

        if binding is None:
            raise DeviceParameterStoreError(
                "unknown adapter/source: "
                + str(adapter_id)
                + " / "
                + str(source_id)
            )

        return self.restore(
            device_id=binding.device_id,
            parameter=binding.parameter,
            value=value,
            available=available,
        )

    def update_source(
        self,
        *,
        adapter_id,
        source_id,
        value,
        available=True,
    ):
        binding = self._registry.resolve_source(
            adapter_id=adapter_id,
            source_id=source_id,
        )

        if binding is None:
            raise DeviceParameterStoreError(
                "unknown adapter/source: "
                + str(adapter_id)
                + " / "
                + str(source_id)
            )

        return self.update(
            device_id=binding.device_id,
            parameter=binding.parameter,
            value=value,
            available=available,
        )

    def get(
        self,
        device_id,
        parameter,
    ):
        with self._lock:
            entry = self._values.get(
                (
                    device_id,
                    parameter,
                )
            )

            return copy.deepcopy(
                entry
            )

    def for_device(
        self,
        device_id,
    ):
        with self._lock:
            entries = [
                entry
                for (
                    current_device_id,
                    _,
                ), entry
                in self._values.items()
                if (
                    current_device_id
                    == device_id
                )
            ]

            entries.sort(
                key=lambda entry: (
                    entry.parameter,
                )
            )

            return copy.deepcopy(
                entries
            )

    def for_location(
        self,
        location_id,
    ):
        with self._lock:
            entries = [
                entry
                for entry
                in self._values.values()
                if (
                    entry.location_id
                    == location_id
                )
            ]

            entries.sort(
                key=lambda entry: (
                    entry.device_id,
                    entry.parameter,
                )
            )

            return copy.deepcopy(
                entries
            )

    def snapshot(self):
        with self._lock:
            entries = list(
                self._values.values()
            )

            entries.sort(
                key=lambda entry: (
                    entry.location_id,
                    entry.device_id,
                    entry.parameter,
                )
            )

            return copy.deepcopy(
                entries
            )

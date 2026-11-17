from __future__ import annotations

from dataclasses import replace

from src.smartscreen_platform.contracts import (
    Observation,
)

from .registry import DeviceRegistry
from .store import DeviceParameterValue


class DeviceObservationBridge:
    def __init__(
        self,
        *,
        registry: DeviceRegistry,
    ):
        self._registry = registry

    def convert(
        self,
        entry: DeviceParameterValue,
        *,
        source_id: str,
    ) -> Observation:
        device = self._registry.get(
            entry.device_id
        )

        if device is None:
            raise ValueError(
                "unknown device_id: "
                + entry.device_id
            )

        definition = device.parameters.get(
            entry.parameter
        )

        if definition is None:
            raise ValueError(
                "unknown parameter for device "
                + entry.device_id
                + ": "
                + entry.parameter
            )

        quality = (
            "good"
            if entry.available
            else "unavailable"
        )

        observation = Observation.create(
            parameter=entry.parameter,
            value=entry.value,
            unit=entry.unit,
            confidence=1.0,
            quality=quality,
            location_id=entry.location_id,
            provenance={
                "provider": device.adapter_id,
                "adapter_id": device.adapter_id,
                "device_id": device.device_id,
                "source_id": source_id,
            },
        )

        return replace(
            observation,
            observed_at=entry.updated_at,
        )

    def _convert_entry(
        self,
        entry: DeviceParameterValue,
    ) -> Observation:
        device = self._registry.get(
            entry.device_id
        )

        if device is None:
            raise ValueError(
                "unknown device_id: "
                + entry.device_id
            )

        definition = device.parameters.get(
            entry.parameter
        )

        if definition is None:
            raise ValueError(
                "unknown parameter for device "
                + entry.device_id
                + ": "
                + entry.parameter
            )

        return self.convert(
            entry,
            source_id=definition.source_id,
        )

    def snapshot(
        self,
        store,
    ):
        return [
            self._convert_entry(
                entry
            )
            for entry in store.snapshot()
        ]

    def for_device(
        self,
        store,
        device_id,
    ):
        return [
            self._convert_entry(
                entry
            )
            for entry in store.for_device(
                device_id
            )
        ]

    def for_location(
        self,
        store,
        location_id,
    ):
        return [
            self._convert_entry(
                entry
            )
            for entry in store.for_location(
                location_id
            )
        ]

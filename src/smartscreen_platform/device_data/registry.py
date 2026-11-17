from __future__ import annotations

from .model import (
    DeviceBinding,
    DeviceDefinition,
)


class DeviceRegistryError(ValueError):
    pass


class DeviceRegistry:
    def __init__(
        self,
        *,
        devices,
    ):
        self._devices = {}
        self._bindings = {}
        self._bindings_by_device_parameter = {}

        for device in devices:
            if not isinstance(
                device,
                DeviceDefinition,
            ):
                raise TypeError(
                    "devices must contain "
                    "DeviceDefinition"
                )

            if (
                device.device_id
                in self._devices
            ):
                raise DeviceRegistryError(
                    "duplicate device_id: "
                    + device.device_id
                )

            self._devices[
                device.device_id
            ] = device

            for (
                parameter,
                definition,
            ) in device.parameters.items():
                source_key = (
                    device.adapter_id,
                    definition.source_id,
                )

                if (
                    source_key
                    in self._bindings
                ):
                    raise DeviceRegistryError(
                        "duplicate adapter/source: "
                        + device.adapter_id
                        + " / "
                        + definition.source_id
                    )

                binding = DeviceBinding(
                    device_id=(
                        device.device_id
                    ),
                    location_id=(
                        definition.observation_location_id
                        or device.location_id
                    ),
                    adapter_id=(
                        device.adapter_id
                    ),
                    source_id=(
                        definition.source_id
                    ),
                    parameter=parameter,
                    value_type=(
                        definition.value_type
                    ),
                    unit=definition.unit,
                )

                self._bindings[
                    source_key
                ] = binding

                self._bindings_by_device_parameter[
                    (
                        device.device_id,
                        parameter,
                    )
                ] = binding

    def get(
        self,
        device_id,
    ):
        return self._devices.get(
            device_id
        )

    def all(self):
        return list(
            self._devices.values()
        )

    def resolve_source(
        self,
        *,
        adapter_id,
        source_id,
    ):
        return self._bindings.get(
            (
                adapter_id,
                source_id,
            )
        )

    def resolve_parameter(
        self,
        *,
        device_id,
        parameter,
    ):
        return (
            self._bindings_by_device_parameter.get(
                (
                    device_id,
                    parameter,
                )
            )
        )

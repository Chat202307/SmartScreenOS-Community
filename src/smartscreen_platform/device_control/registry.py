from __future__ import annotations

from .model import (
    DeviceControlBinding,
)


class DeviceControlRegistryError(
    ValueError
):
    pass


class DeviceControlRegistry:
    def __init__(
        self,
        *,
        bindings,
    ):
        self._bindings = {}
        self._bindings_by_device = {}

        for binding in bindings:
            if not isinstance(
                binding,
                DeviceControlBinding,
            ):
                raise TypeError(
                    "bindings must contain "
                    "DeviceControlBinding"
                )

            key = (
                binding.device_id,
                binding.control.control_id,
            )

            if key in self._bindings:
                raise DeviceControlRegistryError(
                    "duplicate device control: "
                    + binding.device_id
                    + " / "
                    + binding.control.control_id
                )

            self._bindings[
                key
            ] = binding

            self._bindings_by_device.setdefault(
                binding.device_id,
                [],
            ).append(
                binding
            )

    def resolve(
        self,
        *,
        device_id,
        control_id,
    ):
        return self._bindings.get(
            (
                str(device_id),
                str(control_id),
            )
        )

    def for_device(
        self,
        device_id,
    ):
        return list(
            self._bindings_by_device.get(
                str(device_id),
                (),
            )
        )

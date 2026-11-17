from __future__ import annotations

from .model import (
    DeviceControlBinding,
)


def build_device_control_bindings(
    *,
    devices,
):
    bindings = []

    for device in devices:
        for control in (
            device.controls or {}
        ).values():
            bindings.append(
                DeviceControlBinding(
                    device_id=(
                        device.device_id
                    ),
                    adapter_id=(
                        device.adapter_id
                    ),
                    control=control,
                )
            )

    return bindings

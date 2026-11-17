"""Unified device types and capability validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Set


class DeviceTypeError(ValueError):
    pass


@dataclass(frozen=True)
class DeviceTypeSpec:
    name: str
    capabilities: Set[str]


DEVICE_TYPES: Dict[str, DeviceTypeSpec] = {
    "light": DeviceTypeSpec(
        name="light",
        capabilities={
            "turn_on",
            "turn_off",
            "toggle",
            "set_brightness",
            "set_color_temperature",
        },
    ),
    "curtain": DeviceTypeSpec(
        name="curtain",
        capabilities={
            "open",
            "stop",
            "close",
            "set_position",
        },
    ),
    "climate": DeviceTypeSpec(
        name="climate",
        capabilities={
            "turn_off",
            "set_mode",
            "set_temperature",
            "set_fan_mode",
            "set_swing_mode",
        },
    ),
    "occupancy": DeviceTypeSpec(
        name="occupancy",
        capabilities={
            "read_occupancy",
            "read_illuminance",
            "read_battery",
        },
    ),
}


def validate_device_type(device_type: str, capabilities: Iterable[str]) -> None:
    spec = DEVICE_TYPES.get(device_type)
    if spec is None:
        raise DeviceTypeError(f"Unsupported device type: {device_type}")

    invalid = sorted(set(capabilities) - spec.capabilities)
    if invalid:
        raise DeviceTypeError(
            f"Unsupported capabilities for {device_type}: {', '.join(invalid)}"
        )

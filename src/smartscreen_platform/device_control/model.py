from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class DeviceControlDefinition:
    control_id: str
    kind: str
    parameter: str
    options: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None

    def __post_init__(self):
        if not str(self.control_id).strip():
            raise ValueError(
                "control_id is required"
            )

        if not str(self.kind).strip():
            raise ValueError(
                "kind is required"
            )

        if not str(self.parameter).strip():
            raise ValueError(
                "parameter is required"
            )

        options = tuple(
            str(option)
            for option in (
                self.options or ()
            )
        )

        object.__setattr__(
            self,
            "options",
            options,
        )

        for (
            field_name,
            field_value,
        ) in (
            ("minimum", self.minimum),
            ("maximum", self.maximum),
            ("step", self.step),
        ):
            if field_value is None:
                continue

            if (
                isinstance(field_value, bool)
                or not isinstance(
                    field_value,
                    (int, float),
                )
                or not isfinite(
                    float(field_value)
                )
            ):
                raise ValueError(
                    field_name
                    + " must be a finite number"
                )

        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError(
                "minimum must not exceed maximum"
            )

        if (
            self.step is not None
            and self.step <= 0
        ):
            raise ValueError(
                "step must be positive"
            )


@dataclass(frozen=True)
class DeviceControlBinding:
    device_id: str
    adapter_id: str
    control: DeviceControlDefinition

    def __post_init__(self):
        if not str(self.device_id).strip():
            raise ValueError(
                "device_id is required"
            )

        if not str(self.adapter_id).strip():
            raise ValueError(
                "adapter_id is required"
            )

        if not isinstance(
            self.control,
            DeviceControlDefinition,
        ):
            raise TypeError(
                "control must be "
                "DeviceControlDefinition"
            )

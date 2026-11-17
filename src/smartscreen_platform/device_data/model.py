from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.smartscreen_platform.device_control.model import (
    DeviceControlDefinition,
)


@dataclass(frozen=True)
class DeviceParameterDefinition:
    parameter: str
    source_id: str
    value_type: str
    unit: Optional[str] = None
    max_age_seconds: Optional[float] = None
    observation_location_id: Optional[str] = None

    def __post_init__(self):
        if not str(self.parameter).strip():
            raise ValueError(
                "parameter is required"
            )

        if not str(self.source_id).strip():
            raise ValueError(
                "source_id is required"
            )

        if not str(self.value_type).strip():
            raise ValueError(
                "value_type is required"
            )

        if self.max_age_seconds is not None:
            if (
                isinstance(
                    self.max_age_seconds,
                    bool,
                )
                or not isinstance(
                    self.max_age_seconds,
                    (int, float),
                )
                or self.max_age_seconds <= 0
            ):
                raise ValueError(
                    "max_age_seconds must be "
                    "a positive number"
                )


@dataclass(frozen=True)
class DeviceDefinition:
    device_id: str
    name: str
    location_id: str
    adapter_id: str
    parameters: dict[
        str,
        DeviceParameterDefinition,
    ]
    controls: dict[
        str,
        DeviceControlDefinition,
    ] | None = None
    adapter_config: dict | None = None
    power_source_device_id: Optional[str] = None
    power_control_device_id: Optional[str] = None
    area_readonly: bool = False
    device_type: Optional[str] = None

    def __post_init__(self):
        if (
            self.device_type is not None
            and (
                not isinstance(
                    self.device_type,
                    str,
                )
                or not self.device_type.strip()
            )
        ):
            raise ValueError(
                "device_type must be a "
                "non-empty string"
            )

        if not str(self.device_id).strip():
            raise ValueError(
                "device_id is required"
            )

        if not str(self.location_id).strip():
            raise ValueError(
                "location_id is required"
            )

        if not str(self.adapter_id).strip():
            raise ValueError(
                "adapter_id is required"
            )

        if (
            self.power_source_device_id
            is not None
            and (
                not isinstance(
                    self.power_source_device_id,
                    str,
                )
                or not self.power_source_device_id.strip()
            )
        ):
            raise ValueError(
                "power_source_device_id must be "
                "a non-empty string"
            )

        if not isinstance(
            self.area_readonly,
            bool,
        ):
            raise ValueError(
                "area_readonly must be boolean"
            )

        if (
            self.power_control_device_id
            is not None
            and (
                not isinstance(
                    self.power_control_device_id,
                    str,
                )
                or not self.power_control_device_id.strip()
            )
        ):
            raise ValueError(
                "power_control_device_id must be "
                "a non-empty string"
            )

        parameters = dict(
            self.parameters or {}
        )

        controls = dict(
            self.controls or {}
        )

        adapter_config = dict(
            self.adapter_config or {}
        )

        for (
            parameter_name,
            definition,
        ) in parameters.items():
            if (
                not isinstance(
                    definition,
                    DeviceParameterDefinition,
                )
            ):
                raise TypeError(
                    "parameters must contain "
                    "DeviceParameterDefinition"
                )

            if (
                parameter_name
                != definition.parameter
            ):
                raise ValueError(
                    "parameter key must match "
                    "definition.parameter"
                )

        for (
            control_name,
            definition,
        ) in controls.items():
            if (
                not isinstance(
                    definition,
                    DeviceControlDefinition,
                )
            ):
                raise TypeError(
                    "controls must contain "
                    "DeviceControlDefinition"
                )

            if (
                control_name
                != definition.control_id
            ):
                raise ValueError(
                    "control key must match "
                    "definition.control_id"
                )

        object.__setattr__(
            self,
            "parameters",
            parameters,
        )

        object.__setattr__(
            self,
            "controls",
            controls,
        )

        object.__setattr__(
            self,
            "adapter_config",
            adapter_config,
        )



@dataclass(frozen=True)
class DeviceBinding:
    device_id: str
    location_id: str
    adapter_id: str
    source_id: str
    parameter: str
    value_type: str
    unit: Optional[str] = None

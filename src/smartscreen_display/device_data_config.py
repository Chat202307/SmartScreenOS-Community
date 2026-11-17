from __future__ import annotations

import json
from pathlib import Path

from src.smartscreen_platform.device_control import (
    DeviceControlDefinition,
)
from src.smartscreen_platform.device_data import (
    DeviceDefinition,
    DeviceParameterDefinition,
)


SUPPORTED_VALUE_TYPES = {
    "float",
    "int",
    "bool",
    "string",
}


def load_device_definitions(
    path: str | Path,
):
    config_path = Path(path)

    if not config_path.is_file():
        return []

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []

    if not isinstance(payload, dict):
        return []

    devices = payload.get(
        "devices",
        [],
    )

    if not isinstance(devices, list):
        return []

    result = []

    for item in devices:
        if not isinstance(item, dict):
            continue

        device_id = item.get(
            "device_id"
        )
        name = item.get(
            "name"
        )
        location_id = item.get(
            "location_id"
        )
        adapter_id = item.get(
            "adapter_id"
        )
        device_type = item.get(
            "device_type"
        )
        if (
            device_type is not None
            and (
                not isinstance(
                    device_type,
                    str,
                )
                or not device_type.strip()
            )
        ):
            continue

        parameters = item.get(
            "parameters"
        )
        controls = item.get(
            "controls",
            {},
        )
        adapter_config = item.get(
            "adapter_config",
            {},
        )
        power_source_device_id = item.get(
            "power_source_device_id"
        )
        power_control_device_id = item.get(
            "power_control_device_id"
        )
        area_readonly = item.get(
            "area_readonly",
            False,
        )

        if (
            not isinstance(device_id, str)
            or not device_id.strip()
        ):
            continue

        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            continue

        if (
            not isinstance(location_id, str)
            or not location_id.strip()
        ):
            continue

        if (
            not isinstance(adapter_id, str)
            or not adapter_id.strip()
        ):
            continue

        if not isinstance(
            parameters,
            dict,
        ):
            continue

        if not isinstance(
            controls,
            dict,
        ):
            continue

        if not isinstance(
            adapter_config,
            dict,
        ):
            continue

        if (
            power_source_device_id
            is not None
            and (
                not isinstance(
                    power_source_device_id,
                    str,
                )
                or not power_source_device_id.strip()
            )
        ):
            continue

        if not isinstance(
            area_readonly,
            bool,
        ):
            continue

        if (
            power_control_device_id
            is not None
            and (
                not isinstance(
                    power_control_device_id,
                    str,
                )
                or not power_control_device_id.strip()
            )
        ):
            continue

        parameter_definitions = {}
        control_definitions = {}
        valid = True

        for (
            parameter_name,
            definition,
        ) in parameters.items():
            if (
                not isinstance(
                    parameter_name,
                    str,
                )
                or not parameter_name.strip()
            ):
                valid = False
                break

            if not isinstance(
                definition,
                dict,
            ):
                valid = False
                break

            source_id = definition.get(
                "source_id"
            )
            value_type = definition.get(
                "value_type",
                "string",
            )
            unit = definition.get(
                "unit"
            )

            max_age_seconds = definition.get(
                "max_age_seconds"
            )

            observation_location_id = definition.get(
                "observation_location_id"
            )

            if (
                not isinstance(
                    source_id,
                    str,
                )
                or not source_id.strip()
            ):
                valid = False
                break

            if (
                value_type
                not in SUPPORTED_VALUE_TYPES
            ):
                valid = False
                break

            if (
                unit is not None
                and not isinstance(
                    unit,
                    str,
                )
            ):
                valid = False
                break

            if (
                observation_location_id is not None
                and (
                    not isinstance(
                        observation_location_id,
                        str,
                    )
                    or not observation_location_id.strip()
                )
            ):
                valid = False
                break

            if (
                max_age_seconds is not None
                and (
                    isinstance(
                        max_age_seconds,
                        bool,
                    )
                    or not isinstance(
                        max_age_seconds,
                        (int, float),
                    )
                    or max_age_seconds <= 0
                )
            ):
                valid = False
                break

            parameter_definitions[
                parameter_name
            ] = DeviceParameterDefinition(
                parameter=parameter_name,
                source_id=source_id,
                value_type=value_type,
                unit=unit,
                max_age_seconds=(
                    max_age_seconds
                ),
                observation_location_id=(
                    observation_location_id
                ),
            )

        if not valid:
            continue

        for (
            control_name,
            definition,
        ) in controls.items():
            if (
                not isinstance(
                    control_name,
                    str,
                )
                or not control_name.strip()
            ):
                valid = False
                break

            if not isinstance(
                definition,
                dict,
            ):
                valid = False
                break

            kind = definition.get(
                "kind"
            )
            parameter = definition.get(
                "parameter"
            )
            options = definition.get(
                "options",
                [],
            )
            minimum = definition.get(
                "min"
            )
            maximum = definition.get(
                "max"
            )
            step = definition.get(
                "step"
            )

            if (
                not isinstance(
                    kind,
                    str,
                )
                or not kind.strip()
            ):
                valid = False
                break

            if (
                not isinstance(
                    parameter,
                    str,
                )
                or not parameter.strip()
            ):
                valid = False
                break

            if not isinstance(
                options,
                list,
            ):
                valid = False
                break

            if any(
                not isinstance(
                    option,
                    str,
                )
                or not option.strip()
                for option in options
            ):
                valid = False
                break

            try:
                control_definition = (
                    DeviceControlDefinition(
                        control_id=control_name,
                        kind=kind,
                        parameter=parameter,
                        options=tuple(
                            options
                        ),
                        minimum=minimum,
                        maximum=maximum,
                        step=step,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                valid = False
                break

            control_definitions[
                control_name
            ] = control_definition

        if not valid:
            continue

        try:
            device = DeviceDefinition(
                device_id=device_id,
                name=name,
                location_id=location_id,
                adapter_id=adapter_id,
                parameters=(
                    parameter_definitions
                ),
                controls=(
                    control_definitions
                ),
                adapter_config=(
                    adapter_config
                ),
                power_source_device_id=(
                    power_source_device_id
                ),
                power_control_device_id=(
                    power_control_device_id
                ),
                area_readonly=area_readonly,
                device_type=device_type,
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        result.append(
            device
        )

    return result

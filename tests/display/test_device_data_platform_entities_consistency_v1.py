from pathlib import Path

from src.smartscreen_display.device_data_config import (
    load_device_definitions,
)
from src.smartscreen_display.platform_entities_config import (
    load_platform_entities,
)


PROJECT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DEVICE_DATA_CONFIG = (
    PROJECT
    / "config"
    / "device_data.json"
)

PLATFORM_ENTITIES_CONFIG = (
    PROJECT
    / "config"
    / "platform_entities.json"
)


def device_parameter_bindings():
    devices = load_device_definitions(
        DEVICE_DATA_CONFIG
    )

    bindings = {}

    for device in devices:
        if device.adapter_id != "home_assistant":
            continue

        for (
            parameter_name,
            definition,
        ) in device.parameters.items():
            bindings[
                definition.source_id
            ] = {
                "device_id":
                    device.device_id,
                "parameter":
                    parameter_name,
            }

    return bindings


def platform_entity_source_ids():
    return {
        entity["entity_id"]
        for entity in load_platform_entities(
            PLATFORM_ENTITIES_CONFIG
        )
    }





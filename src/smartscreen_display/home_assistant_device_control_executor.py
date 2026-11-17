from __future__ import annotations


class HomeAssistantDeviceControlExecutorError(
    ValueError
):
    pass


class HomeAssistantDeviceControlExecutor:
    ADAPTER_ID = "home_assistant"

    def __init__(
        self,
        *,
        client,
        device_entity_ids,
        device_adapter_configs=None,
    ):
        self._client = client
        self._device_entity_ids = dict(
            device_entity_ids or {}
        )
        self._device_adapter_configs = dict(
            device_adapter_configs or {}
        )

        if not self._device_entity_ids:
            raise (
                HomeAssistantDeviceControlExecutorError(
                    "device mapping must not be empty"
                )
            )

    def execute(
        self,
        *,
        binding,
        value,
    ):
        if (
            binding.adapter_id
            != self.ADAPTER_ID
        ):
            raise (
                HomeAssistantDeviceControlExecutorError(
                    "unsupported adapter: "
                    + str(
                        binding.adapter_id
                    )
                )
            )

        device_id = binding.device_id

        entity_id = (
            self._device_entity_ids.get(
                device_id
            )
        )

        if entity_id is None:
            raise (
                HomeAssistantDeviceControlExecutorError(
                    "unknown home assistant device: "
                    + str(device_id)
                )
            )

        if (
            not isinstance(
                entity_id,
                str,
            )
            or "." not in entity_id
        ):
            raise (
                HomeAssistantDeviceControlExecutorError(
                    "invalid home assistant entity: "
                    + str(entity_id)
                )
            )

        control_id = (
            binding.control.control_id
        )

        if control_id == "power":
            if not isinstance(
                value,
                bool,
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "power value must be boolean"
                    )
                )

            domain = entity_id.split(
                ".",
                1,
            )[0]

            service = (
                "turn_on"
                if value
                else "turn_off"
            )

            return self._client.call_service(
                domain,
                service,
                entity_id,
            )

        climate_controls = {
            "operating_state",
            "target_temperature",
            "fan_mode",
        }

        if control_id in climate_controls:
            if not entity_id.startswith(
                "climate."
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "climate control requires "
                        "climate entity"
                    )
                )

            if control_id == "operating_state":
                if not isinstance(
                    value,
                    str,
                ):
                    raise (
                        HomeAssistantDeviceControlExecutorError(
                            "operating state must be "
                            "a string"
                        )
                    )

                return self._client.call_service(
                    "climate",
                    "set_hvac_mode",
                    entity_id,
                    service_data={
                        "hvac_mode": value,
                    },
                )

            if control_id == "target_temperature":
                try:
                    temperature = float(value)
                except (
                    TypeError,
                    ValueError,
                ) as exc:
                    raise (
                        HomeAssistantDeviceControlExecutorError(
                            "target temperature must "
                            "be numeric"
                        )
                    ) from exc

                return self._client.call_service(
                    "climate",
                    "set_temperature",
                    entity_id,
                    service_data={
                        "temperature": temperature,
                    },
                )

            if not isinstance(
                value,
                str,
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "fan mode must be a string"
                    )
                )

            return self._client.call_service(
                "climate",
                "set_fan_mode",
                entity_id,
                service_data={
                    "fan_mode": value,
                },
            )

        light_number_controls = {
            "brightness",
            "color_temperature",
        }

        if control_id in light_number_controls:
            if not entity_id.startswith(
                "light."
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "light control requires "
                        "light entity"
                    )
                )

            if (
                isinstance(value, bool)
                or not isinstance(
                    value,
                    (int, float),
                )
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "light control value must "
                        "be numeric"
                    )
                )

            numeric_value = float(value)

            if control_id == "brightness":
                service_data = {
                    "brightness_pct":
                        numeric_value,
                }
            else:
                service_data = {
                    "color_temp_kelvin":
                        numeric_value,
                }

            return self._client.call_service(
                "light",
                "turn_on",
                entity_id,
                service_data=service_data,
            )

        if control_id == "return_to_dock":
            if not entity_id.startswith(
                "vacuum."
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "return_to_dock control requires "
                        "vacuum entity"
                    )
                )

            return self._client.call_service(
                "vacuum",
                "return_to_base",
                entity_id,
            )

        if control_id == "clean_all":
            if not entity_id.startswith(
                "vacuum."
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "clean_all control requires "
                        "vacuum entity"
                    )
                )

            adapter_config = (
                self._device_adapter_configs.get(
                    device_id,
                    {}
                )
            )

            clean_all_entity_id = (
                adapter_config.get(
                    "clean_all_entity_id"
                )
            )

            if (
                not isinstance(
                    clean_all_entity_id,
                    str,
                )
                or not clean_all_entity_id.startswith(
                    "button."
                )
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "clean_all entity is not "
                        "configured"
                    )
                )

            return self._client.call_service(
                "button",
                "press",
                clean_all_entity_id,
            )

        if control_id == "clean_areas":
            if not entity_id.startswith(
                "vacuum."
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "clean_areas control requires "
                        "vacuum entity"
                    )
                )

            adapter_config = (
                self._device_adapter_configs.get(
                    device_id,
                    {}
                )
            )

            cleaning_area_ids = (
                adapter_config.get(
                    "cleaning_area_ids",
                    {},
                )
            )

            if not isinstance(
                cleaning_area_ids,
                dict,
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "cleaning area mapping is "
                        "not configured"
                    )
                )

            resolved_area_ids = []

            for location_id in value:
                area_id = cleaning_area_ids.get(
                    location_id
                )

                if (
                    not isinstance(
                        area_id,
                        str,
                    )
                    or not area_id.strip()
                ):
                    raise (
                        HomeAssistantDeviceControlExecutorError(
                            "unknown cleaning area: "
                            + str(location_id)
                        )
                    )

                resolved_area_ids.append(
                    area_id
                )

            return self._client.call_service(
                "vacuum",
                "clean_area",
                entity_id,
                service_data={
                    "cleaning_area_id":
                        resolved_area_ids,
                },
            )

        cover_controls = {
            "state",
            "position",
        }

        if control_id in cover_controls:
            if not entity_id.startswith(
                "cover."
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "cover control requires "
                        "cover entity"
                    )
                )

            if control_id == "state":
                if not isinstance(
                    value,
                    str,
                ):
                    raise (
                        HomeAssistantDeviceControlExecutorError(
                            "unsupported cover state"
                        )
                    )

                services = {
                    "open": "open_cover",
                    "close": "close_cover",
                    "stop": "stop_cover",
                }

                service = services.get(
                    value
                )

                if service is None:
                    raise (
                        HomeAssistantDeviceControlExecutorError(
                            "unsupported cover state"
                        )
                    )

                return self._client.call_service(
                    "cover",
                    service,
                    entity_id,
                )

            try:
                position = int(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "cover position must be "
                        "between 0 and 100"
                    )
                ) from exc

            if (
                position < 0
                or position > 100
            ):
                raise (
                    HomeAssistantDeviceControlExecutorError(
                        "cover position must be "
                        "between 0 and 100"
                    )
                )

            return self._client.call_service(
                "cover",
                "set_cover_position",
                entity_id,
                service_data={
                    "position": position,
                },
            )

        raise (
            HomeAssistantDeviceControlExecutorError(
                "unsupported home assistant control: "
                + str(control_id)
            )
        )

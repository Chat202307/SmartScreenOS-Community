from __future__ import annotations


class DnakeMqttDeviceControlExecutorError(
    ValueError
):
    pass


class DnakeMqttDeviceControlExecutor:
    ADAPTER_ID = "dnake_mqtt"

    CURTAIN_COMMANDS = {
        "open": "OPEN",
        "closed": "CLOSE",
        "stopped": "STOP",
    }

    OPERATING_STATE_COMMANDS = {
        "off": "OFF",
        "cool": "COOL",
        "heat": "HEAT",
    }

    FAN_MODE_COMMANDS = {
        "low": "LOW",
        "medium": "MEDIUM",
    }

    def __init__(
        self,
        *,
        client,
        device_topics,
        device_control_topics=None,
    ):
        self._client = client
        self._device_topics = dict(
            device_topics or {}
        )
        self._device_control_topics = {
            device_id: dict(
                control_topics
            )
            for (
                device_id,
                control_topics,
            )
            in (
                device_control_topics
                or {}
            ).items()
        }

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
                DnakeMqttDeviceControlExecutorError(
                    "unsupported adapter: "
                    + str(
                        binding.adapter_id
                    )
                )
            )

        control_id = (
            binding.control.control_id
        )

        control_topics = (
            self._device_control_topics.get(
                binding.device_id
            )
        )

        if control_topics is not None:
            topic = control_topics.get(
                control_id
            )

            if topic is None:
                raise (
                    DnakeMqttDeviceControlExecutorError(
                        "unsupported dnake mqtt "
                        "control: "
                        + str(control_id)
                    )
                )

            command = (
                self._control_command(
                    control_id=control_id,
                    value=value,
                )
            )

            return self._client.publish(
                topic,
                command,
                retain=False,
            )

        if control_id != "state":
            raise (
                DnakeMqttDeviceControlExecutorError(
                    "unsupported dnake mqtt "
                    "control: "
                    + str(control_id)
                )
            )

        topic = self._device_topics.get(
            binding.device_id
        )

        if topic is None:
            raise (
                DnakeMqttDeviceControlExecutorError(
                    "unknown dnake mqtt device: "
                    + str(binding.device_id)
                )
            )

        try:
            command = (
                self.CURTAIN_COMMANDS[
                    str(value)
                ]
            )
        except KeyError as exc:
            raise (
                DnakeMqttDeviceControlExecutorError(
                    "unsupported curtain command: "
                    + str(value)
                )
            ) from exc

        return self._client.publish(
            topic,
            command,
            retain=False,
        )

    def _control_command(
        self,
        *,
        control_id,
        value,
    ):
        normalized_value = str(value)

        if control_id == "operating_state":
            try:
                return (
                    self.OPERATING_STATE_COMMANDS[
                        normalized_value
                    ]
                )
            except KeyError as exc:
                raise (
                    DnakeMqttDeviceControlExecutorError(
                        "unsupported operating "
                        "state command: "
                        + normalized_value
                    )
                ) from exc

        if control_id == "fan_mode":
            try:
                return (
                    self.FAN_MODE_COMMANDS[
                        normalized_value
                    ]
                )
            except KeyError as exc:
                raise (
                    DnakeMqttDeviceControlExecutorError(
                        "unsupported fan mode "
                        "command: "
                        + normalized_value
                    )
                ) from exc

        if (
            control_id
            == "target_temperature"
        ):
            return normalized_value

        if control_id == "power":
            if value is True:
                return "ON"
            if value is False:
                return "OFF"

            raise (
                DnakeMqttDeviceControlExecutorError(
                    "unsupported power command: "
                    + normalized_value
                )
            )

        raise (
            DnakeMqttDeviceControlExecutorError(
                "unsupported dnake mqtt "
                "control: "
                + str(control_id)
            )
        )

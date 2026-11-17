from __future__ import annotations


class XingooDeviceControllerError(
    ValueError
):
    pass


class XingooDeviceController:
    def __init__(
        self,
        *,
        client,
        device_iot_ids,
    ):
        if not device_iot_ids:
            raise XingooDeviceControllerError(
                "xingoo device mapping "
                "must not be empty"
            )

        self._client = client
        self._device_iot_ids = {
            str(device_id): str(iot_id)
            for (
                device_id,
                iot_id,
            )
            in device_iot_ids.items()
        }

    def _resolve_iot_id(
        self,
        device_id,
    ):
        device_id = str(device_id)

        try:
            return (
                self._device_iot_ids[
                    device_id
                ]
            )

        except KeyError as exc:
            raise (
                XingooDeviceControllerError(
                    "unknown xingoo device: "
                    + device_id
                )
            ) from exc

    def _send_command(
        self,
        device_id,
        command,
    ):
        return self._client.send_command(
            iot_id=self._resolve_iot_id(
                device_id
            ),
            command=command,
        )

    def turn_on(
        self,
        device_id,
    ):
        return self._client.set_power(
            iot_id=self._resolve_iot_id(
                device_id
            ),
            on=True,
        )

    def turn_off(
        self,
        device_id,
    ):
        return self._client.set_power(
            iot_id=self._resolve_iot_id(
                device_id
            ),
            on=False,
        )

    def set_smart_mode(
        self,
        device_id,
    ):
        return self._send_command(
            device_id,
            {
                "WorkMode": 0,
            },
        )

    def set_sleep_mode(
        self,
        device_id,
    ):
        return self._send_command(
            device_id,
            {
                "WorkMode": 2,
            },
        )

    def set_wind_speed(
        self,
        device_id,
        speed,
    ):
        if (
            isinstance(speed, bool)
            or not isinstance(
                speed,
                int,
            )
            or speed < 1
            or speed > 5
        ):
            raise XingooDeviceControllerError(
                "xingoo wind speed "
                "must be between 1 and 5"
            )

        return self._send_command(
            device_id,
            {
                "WindSpeed": speed,
            },
        )

    def set_ions(
        self,
        device_id,
        enabled,
    ):
        if not isinstance(
            enabled,
            bool,
        ):
            raise XingooDeviceControllerError(
                "xingoo ions state "
                "must be boolean"
            )

        return self._send_command(
            device_id,
            {
                "IonsSwitch": (
                    1 if enabled else 0
                ),
            },
        )

    def set_disinfection(
        self,
        device_id,
        enabled,
    ):
        if not isinstance(
            enabled,
            bool,
        ):
            raise XingooDeviceControllerError(
                "xingoo disinfection state "
                "must be boolean"
            )

        return self._send_command(
            device_id,
            {
                "DisinfectSwitch": (
                    1 if enabled else 0
                ),
            },
        )

    def set_screen_on(
        self,
        device_id,
        enabled,
    ):
        if not isinstance(
            enabled,
            bool,
        ):
            raise XingooDeviceControllerError(
                "xingoo screen state "
                "must be boolean"
            )

        # M8 semantics are inverted:
        # ScreenSwitch=0 -> display lit
        # ScreenSwitch=1 -> display dark
        return self._send_command(
            device_id,
            {
                "ScreenSwitch": (
                    0 if enabled else 1
                ),
            },
        )

    def set_child_lock(
        self,
        device_id,
        enabled,
    ):
        if not isinstance(
            enabled,
            bool,
        ):
            raise XingooDeviceControllerError(
                "xingoo child lock state "
                "must be boolean"
            )

        return self._send_command(
            device_id,
            {
                "ChildLockSwitch": (
                    1 if enabled else 0
                ),
            },
        )

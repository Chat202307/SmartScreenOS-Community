from __future__ import annotations


class XingooDeviceControlExecutorError(
    ValueError
):
    pass


class XingooDeviceControlExecutor:
    ADAPTER_ID = "xingoo"

    def __init__(
        self,
        *,
        controller,
    ):
        self._controller = controller

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
                XingooDeviceControlExecutorError(
                    "unsupported adapter: "
                    + str(
                        binding.adapter_id
                    )
                )
            )

        control_id = (
            binding.control.control_id
        )

        device_id = binding.device_id

        if control_id == "power":
            if value:
                return (
                    self._controller
                    .turn_on(
                        device_id
                    )
                )

            return (
                self._controller
                .turn_off(
                    device_id
                )
            )

        if control_id == "mode":
            if value == "smart":
                return (
                    self._controller
                    .set_smart_mode(
                        device_id
                    )
                )

            if value == "sleep":
                return (
                    self._controller
                    .set_sleep_mode(
                        device_id
                    )
                )

            raise (
                XingooDeviceControlExecutorError(
                    "unsupported mode: "
                    + str(value)
                )
            )

        if control_id == "wind_speed":
            try:
                speed = int(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise (
                    XingooDeviceControlExecutorError(
                        "invalid wind speed: "
                        + str(value)
                    )
                ) from exc

            return (
                self._controller
                .set_wind_speed(
                    device_id,
                    speed,
                )
            )

        if control_id == "ions":
            return (
                self._controller
                .set_ions(
                    device_id,
                    value,
                )
            )

        if (
            control_id
            == "disinfection"
        ):
            return (
                self._controller
                .set_disinfection(
                    device_id,
                    value,
                )
            )

        if control_id == "screen_on":
            return (
                self._controller
                .set_screen_on(
                    device_id,
                    value,
                )
            )

        if control_id == "child_lock":
            return (
                self._controller
                .set_child_lock(
                    device_id,
                    value,
                )
            )

        raise (
            XingooDeviceControlExecutorError(
                "unsupported xingoo control: "
                + str(control_id)
            )
        )

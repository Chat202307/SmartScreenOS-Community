from __future__ import annotations

from math import isfinite


class DeviceControlDispatcherError(
    ValueError
):
    pass


class DeviceControlDispatcher:
    def __init__(
        self,
        *,
        registry,
        executors,
    ):
        self._registry = registry
        self._executors = dict(
            executors or {}
        )

    def execute(
        self,
        *,
        device_id,
        control_id,
        value,
    ):
        binding = self._registry.resolve(
            device_id=device_id,
            control_id=control_id,
        )

        if binding is None:
            raise DeviceControlDispatcherError(
                "unknown device control: "
                + str(device_id)
                + " / "
                + str(control_id)
            )

        self._validate_value(
            binding.control,
            value,
        )

        executor = self._executors.get(
            binding.adapter_id
        )

        if executor is None:
            raise DeviceControlDispatcherError(
                "executor unavailable: "
                + binding.adapter_id
            )

        execute = getattr(
            executor,
            "execute",
            None,
        )

        if not callable(execute):
            raise DeviceControlDispatcherError(
                "invalid executor: "
                + binding.adapter_id
            )

        return execute(
            binding=binding,
            value=value,
        )

    @staticmethod
    def _validate_value(
        control,
        value,
    ):
        kind = control.kind

        if kind == "boolean":
            if not isinstance(
                value,
                bool,
            ):
                raise DeviceControlDispatcherError(
                    "boolean control requires "
                    "a boolean value"
                )

            return

        if kind == "select":
            if value not in control.options:
                raise DeviceControlDispatcherError(
                    "value is not an "
                    "allowed option"
                )

            return

        if kind == "action":
            if value is not None:
                raise DeviceControlDispatcherError(
                    "action control requires "
                    "a null value"
                )

            return

        if kind == "multi_select":
            if not isinstance(
                value,
                list,
            ):
                raise DeviceControlDispatcherError(
                    "multi_select control requires "
                    "a list value"
                )

            if not value:
                raise DeviceControlDispatcherError(
                    "multi_select control requires "
                    "at least one option"
                )

            seen = set()

            for option in value:
                if (
                    not isinstance(
                        option,
                        str,
                    )
                    or option
                    not in control.options
                ):
                    raise DeviceControlDispatcherError(
                        "value is not an "
                        "allowed option"
                    )

                if option in seen:
                    raise DeviceControlDispatcherError(
                        "multi_select control contains "
                        "duplicate option"
                    )

                seen.add(option)

            return

        if kind == "number":
            if (
                isinstance(value, bool)
                or not isinstance(
                    value,
                    (int, float),
                )
            ):
                raise DeviceControlDispatcherError(
                    "number control requires "
                    "a numeric value"
                )

            numeric_value = float(value)

            if not isfinite(numeric_value):
                raise DeviceControlDispatcherError(
                    "number control requires "
                    "a finite numeric value"
                )

            if (
                control.minimum is not None
                and numeric_value
                < control.minimum
            ):
                raise DeviceControlDispatcherError(
                    "number control value "
                    "below minimum"
                )

            if (
                control.maximum is not None
                and numeric_value
                > control.maximum
            ):
                raise DeviceControlDispatcherError(
                    "number control value "
                    "above maximum"
                )

            if control.step is not None:
                step_base = (
                    control.minimum
                    if control.minimum is not None
                    else 0.0
                )

                steps = (
                    numeric_value
                    - step_base
                ) / control.step

                if abs(
                    steps - round(steps)
                ) > 1e-9:
                    raise DeviceControlDispatcherError(
                        "number control value "
                        "does not match step"
                    )

            return

        raise DeviceControlDispatcherError(
            "unsupported control kind: "
            + str(kind)
        )

from __future__ import annotations


class HouseholdActionExecutor:
    def __init__(
        self,
        *,
        dispatcher,
        actions=None,
    ):
        self._dispatcher = dispatcher
        self._actions = dict(
            actions or {}
        )

    def execute(
        self,
        action_id,
    ):
        targets = self._actions.get(
            action_id
        )

        if targets is None:
            raise ValueError(
                "unknown household action: "
                + str(action_id)
            )

        succeeded_device_ids = []
        failures = []

        for target in targets:
            device_id = target.get(
                "device_id"
            )
            control_id = target.get(
                "control_id"
            )
            value = target.get(
                "value"
            )

            try:
                self._dispatcher.execute(
                    device_id=device_id,
                    control_id=control_id,
                    value=value,
                )
            except ValueError as exc:
                failures.append(
                    {
                        "device_id":
                            device_id,
                        "error": str(exc),
                    }
                )
                continue

            succeeded_device_ids.append(
                device_id
            )

        status = (
            "success"
            if not failures
            else "partial_failure"
        )

        return {
            "action_id": action_id,
            "status": status,
            "succeeded_device_ids":
                succeeded_device_ids,
            "failures": failures,
        }

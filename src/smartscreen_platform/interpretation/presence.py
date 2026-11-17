from src.smartscreen_platform.contracts import Interpretation

class PresenceInterpreter:
    def __init__(
        self,
        *,
        source_policies=None,
    ):
        self._source_policies = tuple(
            dict(policy)
            for policy in (
                source_policies or ()
            )
            if isinstance(policy, dict)
        )

    def interpret(
        self,
        observations,
        knowledge=None,
        context=None,
    ):
        by_parameter = {
            item.parameter: item
            for item in observations
        }

        presence = by_parameter.get(
            "presence"
        )

        # Direct presence sensors remain authoritative.
        if presence is not None:
            return self._interpret_direct_presence(
                by_parameter,
                presence,
            )

        motion = by_parameter.get(
            "motion_idle_seconds"
        )

        if motion is None:
            return []

        policy = self._motion_policy_for(
            motion
        )

        if policy is None:
            return []

        settings = policy.get(
            "settings",
            {},
        )

        threshold = settings.get(
            "occupied_below_seconds"
        )

        try:
            idle_seconds = float(
                motion.value
            )
            threshold_seconds = float(
                threshold
            )
        except (TypeError, ValueError):
            return []

        if idle_seconds < threshold_seconds:
            state = "occupied"
            value = None
        else:
            state = "unoccupied"
            value = 0

        return [
            Interpretation.create(
                interpretation_type=(
                    "occupancy_state"
                ),
                name=state,
                value=value,
                confidence=float(
                    motion.confidence
                ),
                location_id=(
                    motion.location_id
                ),
                evidence_refs=[
                    motion.observation_id,
                ],
                expires_in_seconds=60,
            )
        ]

    def _interpret_direct_presence(
        self,
        by_parameter,
        presence,
    ):
        count = by_parameter.get(
            "occupancy_count"
        )

        if not bool(presence.value):
            state = "unoccupied"
            value = 0
        elif count is not None:
            state = "occupied"
            value = int(
                count.value
            )
        else:
            state = "occupied"
            value = None

        confidence = float(
            presence.confidence
        )

        if count is not None:
            confidence = min(
                confidence,
                float(count.confidence),
            )

        return [
            Interpretation.create(
                interpretation_type=(
                    "occupancy_state"
                ),
                name=state,
                value=value,
                confidence=confidence,
                location_id=(
                    presence.location_id
                ),
                evidence_refs=[
                    item.observation_id
                    for item
                    in by_parameter.values()
                ],
                expires_in_seconds=60,
            )
        ]

    def _motion_policy_for(
        self,
        observation,
    ):
        provenance = getattr(
            observation,
            "provenance",
            {},
        )

        if not isinstance(
            provenance,
            dict,
        ):
            provenance = {}

        entity_id = provenance.get(
            "entity_id"
        )

        for policy in self._source_policies:
            if (
                policy.get("strategy")
                != "motion_idle_threshold"
            ):
                continue

            if (
                policy.get("parameter")
                != "motion_idle_seconds"
            ):
                continue

            if (
                policy.get("location_id")
                != observation.location_id
            ):
                continue

            if (
                policy.get("entity_id")
                != entity_id
            ):
                continue

            return policy

        return None

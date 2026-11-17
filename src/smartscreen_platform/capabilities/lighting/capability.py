from src.smartscreen_platform.contracts.state import (
    StatePatch,
)


class LightingCapability:
    """Project lighting interpretations into household state."""

    name = "lighting"
    managed_targets = (
        "lighting",
    )

    def evaluate(
        self,
        interpretations,
        observations=None,
        knowledge=None,
    ):
        lighting = next(
            (
                item
                for item in interpretations
                if item.interpretation_type
                == "lighting_state"
            ),
            None,
        )

        if lighting is None:
            return []

        return [
            StatePatch.create(
                capability=self.name,
                target="lighting",
                value={
                    "state": str(
                        lighting.value
                    ),
                },
                confidence=(
                    lighting.confidence
                ),
                ttl_seconds=(
                    lighting.expires_in_seconds
                ),
                location_id=(
                    lighting.location_id
                ),
                evidence_refs=(
                    lighting.evidence_refs
                ),
                metadata={
                    "model": "lighting_v1",
                },
            )
        ]

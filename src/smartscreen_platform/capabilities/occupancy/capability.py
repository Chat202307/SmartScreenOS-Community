from src.smartscreen_platform.contracts.state import (
    StatePatch,
)


class OccupancyCapability:
    """Project occupancy interpretations into household state."""

    name = "occupancy"
    managed_targets = ("occupancy",)

    def evaluate(
        self,
        interpretations,
        observations=None,
        knowledge=None,
    ):
        occupancy = next(
            (
                item
                for item in interpretations
                if item.interpretation_type
                == "occupancy_state"
            ),
            None,
        )

        if occupancy is None:
            return []

        return [
            StatePatch.create(
                capability=self.name,
                target="occupancy",
                value={
                    "state": occupancy.name,
                    "count": occupancy.value,
                },
                confidence=occupancy.confidence,
                ttl_seconds=(
                    occupancy.expires_in_seconds
                ),
                location_id=occupancy.location_id,
                evidence_refs=occupancy.evidence_refs,
                metadata={
                    "model": "occupancy_v1",
                },
            )
        ]

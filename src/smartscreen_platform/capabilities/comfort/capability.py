from src.smartscreen_platform.contracts.state import StatePatch
from .model import ComfortState


class ComfortCapability:
    name = "comfort"
    managed_targets = ("comfort",)

    def evaluate(self, interpretations, observations=None, knowledge=None):
        observations = list(observations or [])
        by_interpretation = {
            item.interpretation_type: item for item in interpretations
        }
        by_observation = {
            item.parameter: item for item in observations
        }

        thermal = by_interpretation.get("thermal_state")
        if thermal is None:
            return []

        humidity = by_observation.get("humidity")
        if humidity is None:
            return []

        location_id = thermal.location_id
        dimensions = {"thermal": str(thermal.value)}
        penalties = 0
        completeness = 0.55
        evidence = list(thermal.evidence_refs)

        thermal_penalty = {
            "comfortable": 0,
            "cool": 12,
            "warm": 15,
            "cold": 30,
            "hot": 35,
        }.get(str(thermal.value), 20)
        penalties += thermal_penalty

        lighting = by_interpretation.get(
            "lighting_state"
        )

        if lighting is not None:
            completeness += 0.15

            evidence.extend(
                lighting.evidence_refs
            )

            lighting_state = str(
                lighting.value
            )

            dimensions["lighting"] = (
                lighting_state
            )

            if lighting_state == "dim":
                penalties += 8
            elif lighting_state == "bright":
                penalties += 7

        noise = by_observation.get("noise_level")
        if noise is not None:
            completeness += 0.15
            evidence.append(noise.observation_id)
            db = float(noise.value)
            if db > 70:
                dimensions["acoustic"] = "noisy"
                penalties += 15
            elif db > 55:
                dimensions["acoustic"] = "active"
                penalties += 5
            else:
                dimensions["acoustic"] = "quiet"

        completeness += 0.15
        evidence.append(humidity.observation_id)
        value = float(humidity.value)
        if value > 70:
            dimensions["humidity"] = "high"
            penalties += 10
        elif value < 30:
            dimensions["humidity"] = "low"
            penalties += 8
        else:
            dimensions["humidity"] = "comfortable"

        score = max(0, min(100, 100 - penalties))
        confidence = min(
            float(thermal.confidence),
            completeness,
        )

        if score >= 85:
            level = "comfortable"
            summary = "当前空间整体比较舒适。"
        elif score >= 65:
            level = "slightly_uncomfortable"
            summary = "当前空间有轻微不舒适，但未必需要打扰。"
        else:
            level = "uncomfortable"
            summary = "当前空间舒适度较低，值得关注。"

        state = ComfortState(
            level=level,
            score=score,
            confidence=confidence,
            location_id=location_id,
            summary=summary,
            dimensions=dimensions,
            evidence_refs=sorted(set(evidence)),
        )

        return [
            StatePatch.create(
                capability=self.name,
                target="comfort",
                value=state.to_dict(),
                confidence=confidence,
                ttl_seconds=300,
                location_id=location_id,
                evidence_refs=state.evidence_refs,
                metadata={
                    "model": "comfort_v1",
                    "complete_dimensions": len(dimensions),
                },
            )
        ]

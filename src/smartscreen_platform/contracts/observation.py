from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

@dataclass(frozen=True)
class Observation:
    observation_id: str
    parameter: str
    value: Any
    observed_at: str
    unit: Optional[str] = None
    confidence: float = 1.0
    quality: str = "good"
    location_id: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        parameter,
        value,
        unit=None,
        confidence=1.0,
        quality="good",
        location_id=None,
        provenance=None,
        metadata=None,
    ):
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not str(parameter).strip():
            raise ValueError("parameter is required")

        return cls(
            observation_id=f"obs-{uuid4()}",
            parameter=str(parameter),
            value=value,
            observed_at=datetime.now(timezone.utc).isoformat(),
            unit=unit,
            confidence=confidence,
            quality=str(quality),
            location_id=location_id,
            provenance=dict(provenance or {}),
            metadata=dict(metadata or {}),
        )

    def to_dict(self):
        return {
            "observation_id": self.observation_id,
            "parameter": self.parameter,
            "value": self.value,
            "observed_at": self.observed_at,
            "unit": self.unit,
            "confidence": self.confidence,
            "quality": self.quality,
            "location_id": self.location_id,
            "provenance": dict(self.provenance),
            "metadata": dict(self.metadata),
        }

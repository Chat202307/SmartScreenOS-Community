from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Interpretation:
    interpretation_type: str
    name: str
    value: Any
    confidence: float
    created_at: str
    location_id: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    expires_in_seconds: int = 120
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not str(self.interpretation_type).strip():
            raise ValueError("interpretation_type is required")
        if not str(self.name).strip():
            raise ValueError("name is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if int(self.expires_in_seconds) <= 0:
            raise ValueError("expires_in_seconds must be greater than zero")

    @classmethod
    def create(
        cls,
        interpretation_type,
        name,
        value,
        confidence,
        location_id=None,
        evidence_refs=None,
        expires_in_seconds=120,
        metadata=None,
    ):
        return cls(
            interpretation_type=str(interpretation_type),
            name=str(name),
            value=value,
            confidence=float(confidence),
            created_at=datetime.now(timezone.utc).isoformat(),
            location_id=location_id,
            evidence_refs=list(evidence_refs or []),
            expires_in_seconds=int(expires_in_seconds),
            metadata=dict(metadata or {}),
        )

    def to_dict(self):
        return {
            "interpretation_type": self.interpretation_type,
            "name": self.name,
            "value": self.value,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "location_id": self.location_id,
            "evidence_refs": list(self.evidence_refs),
            "expires_in_seconds": self.expires_in_seconds,
            "metadata": dict(self.metadata),
        }

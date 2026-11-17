from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class StatePatch:
    capability: str
    target: str
    value: Any
    confidence: float
    ttl_seconds: int
    created_at: str
    location_id: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        capability,
        target,
        value,
        confidence,
        ttl_seconds,
        location_id=None,
        evidence_refs=None,
        metadata=None,
    ):
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if int(ttl_seconds) <= 0:
            raise ValueError("ttl_seconds must be greater than zero")

        return cls(
            capability=str(capability),
            target=str(target),
            value=value,
            confidence=confidence,
            ttl_seconds=int(ttl_seconds),
            created_at=datetime.now(timezone.utc).isoformat(),
            location_id=location_id,
            evidence_refs=list(evidence_refs or []),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class HouseholdStateEntry:
    target: str
    value: Any
    confidence: float
    updated_at: str
    ttl_seconds: int
    location_id: Optional[str] = None
    source_capability: Optional[str] = None
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "target": self.target,
            "value": self.value,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
            "ttl_seconds": self.ttl_seconds,
            "location_id": self.location_id,
            "source_capability": self.source_capability,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
        }

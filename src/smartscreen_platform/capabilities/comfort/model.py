from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ComfortState:
    level: str
    score: int
    confidence: float
    location_id: Optional[str]
    summary: str
    dimensions: Dict[str, str] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.level not in {
            "comfortable",
            "slightly_uncomfortable",
            "uncomfortable",
            "unknown",
        }:
            raise ValueError("invalid comfort level")
        if not 0 <= int(self.score) <= 100:
            raise ValueError("score must be between 0 and 100")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self):
        return {
            "level": self.level,
            "score": self.score,
            "confidence": self.confidence,
            "location_id": self.location_id,
            "summary": self.summary,
            "dimensions": dict(self.dimensions),
            "evidence_refs": list(self.evidence_refs),
        }

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Evidence:
    source: str
    fact: str
    value: Any
    confidence: float = 1.0


@dataclass(frozen=True)
class Experience:
    room_id: Optional[str]
    category: str
    level: str
    summary: str
    confidence: float
    evidence: List[Evidence] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExpressionProposal:
    action: str
    human_value: str
    priority: str
    requires_attention: bool
    experience: Optional[Experience] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

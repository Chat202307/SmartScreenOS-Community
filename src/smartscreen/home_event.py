from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

@dataclass(frozen=True)
class HomeEvent:
    event_type: str
    source: str
    created_at: str
    room_id: Optional[str] = None
    device_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, event_type, source, room_id=None, device_id=None, payload=None):
        return cls(
            event_type=str(event_type),
            source=str(source),
            created_at=datetime.now(timezone.utc).isoformat(),
            room_id=room_id,
            device_id=device_id,
            payload=dict(payload or {}),
        )

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "source": self.source,
            "created_at": self.created_at,
            "room_id": self.room_id,
            "device_id": self.device_id,
            "payload": dict(self.payload),
        }

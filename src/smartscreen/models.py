from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass(frozen=True)
class Room:
    id: str
    name: str
    area: str
    order: int = 0

@dataclass(frozen=True)
class Device:
    id: str
    name: str
    room: str
    type: str
    adapter: str
    capabilities: List[str] = field(default_factory=list)
    adapter_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeviceState:
    device_id: str
    available: bool = False
    state: str = "unknown"
    attributes: Dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""

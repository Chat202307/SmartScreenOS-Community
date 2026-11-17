from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CapabilityManifest:
    manifest_version: str
    capability_id: str
    name: str
    category: str
    version: str
    provider: str
    description: str = ""
    entry_point: str = ""
    contracts: tuple[str, ...] = ()
    required_dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)

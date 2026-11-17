from __future__ import annotations

from dataclasses import dataclass

from ..manifest.model import CapabilityManifest
from .state import RuntimeState


@dataclass(slots=True)
class CapabilitySession:
    session_id: str
    manifest: CapabilityManifest
    state: RuntimeState

    @property
    def capability_id(self) -> str:
        return self.manifest.capability_id

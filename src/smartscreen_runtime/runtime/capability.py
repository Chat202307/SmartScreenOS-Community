from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..manifest.model import CapabilityManifest


@dataclass(frozen=True, slots=True)
class CapabilityRuntime:
    """A validated capability prepared for use by the runtime."""

    root_path: Path
    manifest_path: Path
    manifest: CapabilityManifest

    @property
    def capability_id(self) -> str:
        return self.manifest.capability_id

    @property
    def entry_point(self) -> str:
        return self.manifest.entry_point

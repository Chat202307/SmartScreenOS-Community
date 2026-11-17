from __future__ import annotations

from collections.abc import Iterable

from ..manifest.model import CapabilityManifest
from .errors import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotFoundError,
)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, CapabilityManifest] = {}

    def register(self, manifest: CapabilityManifest) -> None:
        capability_id = manifest.capability_id

        if capability_id in self._manifests:
            raise CapabilityAlreadyRegisteredError(
                f"Capability already registered: {capability_id}"
            )

        self._manifests[capability_id] = manifest

    def unregister(self, capability_id: str) -> CapabilityManifest:
        try:
            return self._manifests.pop(capability_id)
        except KeyError as exc:
            raise CapabilityNotFoundError(
                f"Capability not found: {capability_id}"
            ) from exc

    def get(self, capability_id: str) -> CapabilityManifest:
        try:
            return self._manifests[capability_id]
        except KeyError as exc:
            raise CapabilityNotFoundError(
                f"Capability not found: {capability_id}"
            ) from exc

    def list(self) -> tuple[CapabilityManifest, ...]:
        return tuple(self._manifests.values())

    def __len__(self) -> int:
        return len(self._manifests)

    def __iter__(self) -> Iterable[CapabilityManifest]:
        return iter(self._manifests.values())

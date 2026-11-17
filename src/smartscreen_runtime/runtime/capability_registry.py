from __future__ import annotations

from .capability import CapabilityRuntime


class CapabilityRegistryError(Exception):
    """Base exception for capability registry errors."""


class CapabilityAlreadyRegisteredError(CapabilityRegistryError):
    """Raised when a capability ID is already registered."""


class CapabilityNotRegisteredError(CapabilityRegistryError):
    """Raised when a capability ID is not registered."""


class CapabilityRegistry:
    """Store and manage loaded capability runtime objects."""

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityRuntime] = {}

    def register(
        self,
        capability: CapabilityRuntime,
    ) -> CapabilityRuntime:
        capability_id = capability.capability_id

        if capability_id in self._capabilities:
            raise CapabilityAlreadyRegisteredError(
                f"Capability already registered: {capability_id}"
            )

        self._capabilities[capability_id] = capability
        return capability

    def get(self, capability_id: str) -> CapabilityRuntime:
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise CapabilityNotRegisteredError(
                f"Capability not registered: {capability_id}"
            ) from exc

    def list(self) -> tuple[CapabilityRuntime, ...]:
        return tuple(self._capabilities.values())

    def unregister(self, capability_id: str) -> CapabilityRuntime:
        try:
            return self._capabilities.pop(capability_id)
        except KeyError as exc:
            raise CapabilityNotRegisteredError(
                f"Capability not registered: {capability_id}"
            ) from exc

    def __contains__(self, capability_id: object) -> bool:
        return capability_id in self._capabilities

    def __len__(self) -> int:
        return len(self._capabilities)

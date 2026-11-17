from __future__ import annotations

from ..manifest.model import CapabilityManifest
from ..registry.registry import CapabilityRegistry
from .lifecycle import CapabilityLifecycle
from .state import RuntimeState
from .state_store import CapabilityStateStore


class RuntimeCore:
    def __init__(
        self,
        registry: CapabilityRegistry,
        state_store: CapabilityStateStore | None = None,
        lifecycle: CapabilityLifecycle | None = None,
    ) -> None:
        self._registry = registry
        self._state_store = state_store or CapabilityStateStore()
        self._lifecycle = lifecycle or CapabilityLifecycle()

    def install(self, manifest: CapabilityManifest) -> None:
        capability_id = manifest.capability_id
        current_state = self._state_store.get(capability_id)

        self._lifecycle.validate_transition(
            current_state,
            RuntimeState.INSTALLED,
        )

        self._registry.register(manifest)
        self._state_store.set(
            capability_id,
            RuntimeState.INSTALLED,
        )

    def activate(self, capability_id: str) -> None:
        self._registry.get(capability_id)
        current_state = self._state_store.get(capability_id)

        self._lifecycle.validate_transition(
            current_state,
            RuntimeState.ACTIVE,
        )

        self._state_store.set(
            capability_id,
            RuntimeState.ACTIVE,
        )

    def deactivate(self, capability_id: str) -> None:
        self._registry.get(capability_id)
        current_state = self._state_store.get(capability_id)

        self._lifecycle.validate_transition(
            current_state,
            RuntimeState.INACTIVE,
        )

        self._state_store.set(
            capability_id,
            RuntimeState.INACTIVE,
        )

    def uninstall(self, capability_id: str) -> None:
        self._registry.get(capability_id)
        current_state = self._state_store.get(capability_id)

        self._lifecycle.validate_transition(
            current_state,
            RuntimeState.UNINSTALLED,
        )

        self._registry.unregister(capability_id)
        self._state_store.set(
            capability_id,
            RuntimeState.UNINSTALLED,
        )

    def state(self, capability_id: str) -> RuntimeState:
        return self._state_store.get(capability_id)

from __future__ import annotations

from .state import RuntimeState


class CapabilityStateStore:
    def __init__(self) -> None:
        self._states: dict[str, RuntimeState] = {}

    def get(self, capability_id: str) -> RuntimeState:
        return self._states.get(
            capability_id,
            RuntimeState.UNINSTALLED,
        )

    def set(
        self,
        capability_id: str,
        state: RuntimeState,
    ) -> None:
        self._states[capability_id] = state

    def remove(self, capability_id: str) -> None:
        self._states.pop(capability_id, None)

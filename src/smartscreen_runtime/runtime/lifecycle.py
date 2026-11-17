from __future__ import annotations

from .errors import InvalidRuntimeStateError
from .state import RuntimeState


class CapabilityLifecycle:
    _ALLOWED_TRANSITIONS: dict[RuntimeState, frozenset[RuntimeState]] = {
        RuntimeState.UNINSTALLED: frozenset({
            RuntimeState.INSTALLED,
        }),
        RuntimeState.INSTALLED: frozenset({
            RuntimeState.ACTIVE,
            RuntimeState.UNINSTALLED,
        }),
        RuntimeState.ACTIVE: frozenset({
            RuntimeState.INACTIVE,
        }),
        RuntimeState.INACTIVE: frozenset({
            RuntimeState.ACTIVE,
            RuntimeState.UNINSTALLED,
        }),
    }

    def can_transition(
        self,
        current_state: RuntimeState,
        target_state: RuntimeState,
    ) -> bool:
        return target_state in self._ALLOWED_TRANSITIONS.get(
            current_state,
            frozenset(),
        )

    def validate_transition(
        self,
        current_state: RuntimeState,
        target_state: RuntimeState,
    ) -> None:
        if not self.can_transition(current_state, target_state):
            raise InvalidRuntimeStateError(
                f"Invalid lifecycle transition: "
                f"{current_state.value} -> {target_state.value}"
            )

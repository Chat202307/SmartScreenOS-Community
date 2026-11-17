from __future__ import annotations

from ..manifest.model import CapabilityManifest
from .session import CapabilitySession
from .state import RuntimeState


class CapabilitySessionError(Exception):
    """Base exception for capability session manager errors."""


class CapabilitySessionAlreadyExistsError(CapabilitySessionError):
    """Raised when a session with the same ID already exists."""


class CapabilitySessionNotFoundError(CapabilitySessionError):
    """Raised when a requested session does not exist."""


class CapabilitySessionManager:
    """Creates, stores, retrieves, lists, and removes capability sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, CapabilitySession] = {}

    def create(
        self,
        session_id: str,
        manifest: CapabilityManifest,
        state: RuntimeState,
    ) -> CapabilitySession:
        if session_id in self._sessions:
            raise CapabilitySessionAlreadyExistsError(
                f"Capability session already exists: {session_id}"
            )

        session = CapabilitySession(
            session_id=session_id,
            manifest=manifest,
            state=state,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> CapabilitySession:
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise CapabilitySessionNotFoundError(
                f"Capability session not found: {session_id}"
            ) from exc

    def list(self) -> tuple[CapabilitySession, ...]:
        return tuple(self._sessions.values())

    def list_by_capability(
        self,
        capability_id: str,
    ) -> tuple[CapabilitySession, ...]:
        return tuple(
            session
            for session in self._sessions.values()
            if session.capability_id == capability_id
        )

    def list_active_by_capability(
        self,
        capability_id: str,
    ) -> tuple[CapabilitySession, ...]:
        active_states = {
            RuntimeState.STARTING,
            RuntimeState.RUNNING,
            RuntimeState.STOPPING,
        }

        return tuple(
            session
            for session in self.list_by_capability(capability_id)
            if session.state in active_states
        )

    def update_state(
        self,
        session_id: str,
        state: RuntimeState,
    ) -> CapabilitySession:
        session = self.get(session_id)
        session.state = state
        return session

    def remove(self, session_id: str) -> CapabilitySession:
        try:
            return self._sessions.pop(session_id)
        except KeyError as exc:
            raise CapabilitySessionNotFoundError(
                f"Capability session not found: {session_id}"
            ) from exc

    def __len__(self) -> int:
        return len(self._sessions)

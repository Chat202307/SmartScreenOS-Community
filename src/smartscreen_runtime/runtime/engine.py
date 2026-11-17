from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .capability import CapabilityRuntime
from .capability_api import CapabilityContext
from .capability_factory import CapabilityFactory
from .capability_loader import CapabilityLoader
from .capability_registry import CapabilityRegistry
from .session import CapabilitySession
from .session_manager import CapabilitySessionManager
from .state import RuntimeState
from .snapshot_schema import RuntimeSnapshot


@dataclass(frozen=True, slots=True)
class CapabilityTickResult:
    """Result of one capability maintenance hook execution."""

    session_id: str
    success: bool
    error: Exception | None = None


@dataclass(frozen=True, slots=True)
class CapabilityTickHealth:
    """Health history for a capability maintenance hook."""

    session_id: str
    consecutive_failures: int
    last_error: Exception | None
    last_success_at: datetime | None
    last_failure_at: datetime | None


class CapabilityTickHealthStatus(str, Enum):
    """Derived health level for a capability maintenance hook."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class RuntimeEngineError(Exception):
    """Base exception for runtime engine errors."""


class CapabilityInstanceNotFoundError(RuntimeEngineError):
    """Raised when no running instance exists for a session."""


class CapabilityTickHealthNotFoundError(RuntimeEngineError):
    """Raised when no tick health exists for a session."""


class CapabilityHasActiveSessionsError(RuntimeEngineError):
    """Raised when uninstall is requested while sessions are active."""


class CapabilityStartError(RuntimeEngineError):
    """Raised when a capability instance cannot be started."""


class CapabilityStopError(RuntimeEngineError):
    """Raised when a capability instance cannot be stopped."""


class RuntimeEngine:
    """Coordinate capability installation, execution, and sessions."""

    def __init__(
        self,
        loader: CapabilityLoader | None = None,
        registry: CapabilityRegistry | None = None,
        sessions: CapabilitySessionManager | None = None,
        factory: CapabilityFactory | None = None,
    ) -> None:
        self.loader = loader or CapabilityLoader()
        self.registry = registry or CapabilityRegistry()
        self.sessions = sessions or CapabilitySessionManager()
        self.factory = factory or CapabilityFactory()

        self._instances: dict[str, Any] = {}
        self._tick_health: dict[str, CapabilityTickHealth] = {}

    def install(
        self,
        capability_path: str | Path,
    ) -> CapabilityRuntime:
        capability = self.loader.load(capability_path)
        return self.registry.register(capability)

    def uninstall(self, capability_id: str) -> CapabilityRuntime:
        active_sessions = self.sessions.list_active_by_capability(
            capability_id
        )

        if active_sessions:
            session_ids = ", ".join(
                session.session_id for session in active_sessions
            )
            raise CapabilityHasActiveSessionsError(
                f"Capability has active sessions "
                f"{capability_id}: {session_ids}"
            )

        return self.registry.unregister(capability_id)

    def installed(self) -> tuple[CapabilityRuntime, ...]:
        return self.registry.list()

    def start(
        self,
        capability_id: str,
        session_id: str | None = None,
        configuration: dict[str, object] | None = None,
    ) -> CapabilitySession:
        capability = self.registry.get(capability_id)
        resolved_session_id = session_id or str(uuid4())

        session = self.sessions.create(
            session_id=resolved_session_id,
            manifest=capability.manifest,
            state=RuntimeState.STARTING,
        )

        try:
            instance = self.factory.create(capability)

            logger = logging.getLogger(
                f"smartscreen.capability."
                f"{capability.capability_id}."
                f"{session.session_id}"
            )

            resolved_configuration = dict(
                capability.manifest.configuration
            )
            if configuration is not None:
                resolved_configuration.update(configuration)

            context = CapabilityContext(
                session_id=session.session_id,
                capability_id=capability.capability_id,
                configuration=resolved_configuration,
                logger=logger,
            )

            instance.start(context)
        except Exception as exc:
            self.sessions.update_state(
                session.session_id,
                RuntimeState.FAILED,
            )
            raise CapabilityStartError(
                f"Unable to start capability {capability_id}: {exc}"
            ) from exc

        self._instances[session.session_id] = instance
        self.sessions.update_state(
            session.session_id,
            RuntimeState.RUNNING,
        )
        return session

    def stop(self, session_id: str) -> CapabilitySession:
        session = self.sessions.get(session_id)
        instance = self.get_instance(session_id)

        self.sessions.update_state(
            session_id,
            RuntimeState.STOPPING,
        )

        try:
            instance.stop()
        except Exception as exc:
            self.sessions.update_state(
                session_id,
                RuntimeState.FAILED,
            )
            raise CapabilityStopError(
                f"Unable to stop capability session: {session_id}"
            ) from exc

        del self._instances[session_id]
        self._tick_health.pop(session_id, None)

        self.sessions.update_state(
            session_id,
            RuntimeState.STOPPED,
        )
        return session

    def tick(self) -> dict[str, CapabilityTickResult]:
        """Run one isolated maintenance cycle for active capabilities."""

        results: dict[str, CapabilityTickResult] = {}

        for session in self.sessions.list():
            if session.state is not RuntimeState.RUNNING:
                continue

            instance = self._instances.get(session.session_id)
            if instance is None:
                continue

            refresh_if_stale = getattr(
                instance,
                "refresh_if_stale",
                None,
            )

            if not callable(refresh_if_stale):
                continue

            now = datetime.now(timezone.utc)
            previous = self._tick_health.get(session.session_id)

            try:
                refresh_if_stale()
            except Exception as exc:
                consecutive_failures = (
                    previous.consecutive_failures + 1
                    if previous is not None
                    else 1
                )

                self._tick_health[
                    session.session_id
                ] = CapabilityTickHealth(
                    session_id=session.session_id,
                    consecutive_failures=consecutive_failures,
                    last_error=exc,
                    last_success_at=(
                        previous.last_success_at
                        if previous is not None
                        else None
                    ),
                    last_failure_at=now,
                )

                results[session.session_id] = CapabilityTickResult(
                    session_id=session.session_id,
                    success=False,
                    error=exc,
                )
                continue

            self._tick_health[
                session.session_id
            ] = CapabilityTickHealth(
                session_id=session.session_id,
                consecutive_failures=0,
                last_error=None,
                last_success_at=now,
                last_failure_at=(
                    previous.last_failure_at
                    if previous is not None
                    else None
                ),
            )

            results[session.session_id] = CapabilityTickResult(
                session_id=session.session_id,
                success=True,
                error=None,
            )

        return results

    def snapshot(self) -> RuntimeSnapshot:
        installed_snapshot: list[dict[str, object]] = []

        for capability in self.registry.list():
            installed_snapshot.append(
                {
                    "capabilityId": capability.capability_id,
                    "name": capability.manifest.name,
                    "version": capability.manifest.version,
                }
            )

        session_snapshot: list[dict[str, object]] = []

        for session in self.sessions.list():
            health = self._tick_health.get(session.session_id)

            if health is None:
                tick_health = None
                consecutive_failures = 0
                last_error = None
            else:
                tick_health = self.get_tick_health_status(
                    session.session_id
                ).value
                consecutive_failures = health.consecutive_failures
                last_error = (
                    str(health.last_error)
                    if health.last_error is not None
                    else None
                )

            session_snapshot.append(
                {
                    "sessionId": session.session_id,
                    "capabilityId": session.capability_id,
                    "state": session.state.value,
                    "tickHealth": tick_health,
                    "consecutiveFailures": consecutive_failures,
                    "lastError": last_error,
                }
            )

        return {
            "installed": installed_snapshot,
            "sessions": session_snapshot,
        }

    def get_tick_health_summary(
        self,
    ) -> dict[str, CapabilityTickHealthStatus]:
        return {
            session_id: self.get_tick_health_status(session_id)
            for session_id in self._tick_health
        }

    def get_tick_health_status(
        self,
        session_id: str,
    ) -> CapabilityTickHealthStatus:
        health = self.get_tick_health(session_id)

        if health.consecutive_failures == 0:
            return CapabilityTickHealthStatus.HEALTHY

        if health.consecutive_failures < 3:
            return CapabilityTickHealthStatus.DEGRADED

        return CapabilityTickHealthStatus.UNHEALTHY

    def get_tick_health(
        self,
        session_id: str,
    ) -> CapabilityTickHealth:
        try:
            return self._tick_health[session_id]
        except KeyError as exc:
            raise CapabilityTickHealthNotFoundError(
                f"Capability tick health not found: {session_id}"
            ) from exc

    def list_instances(
        self,
    ) -> tuple[tuple[str, Any], ...]:
        """Return running capability instances in insertion order."""

        return tuple(self._instances.items())

    def get_instance(self, session_id: str) -> Any:
        try:
            return self._instances[session_id]
        except KeyError as exc:
            raise CapabilityInstanceNotFoundError(
                f"Capability instance not found: {session_id}"
            ) from exc

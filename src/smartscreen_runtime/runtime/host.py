from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Callable
from typing import Any

from .engine import RuntimeEngine
from .scheduler import RuntimeScheduler
from .snapshot_schema import (
    HostSnapshot,
    SNAPSHOT_SCHEMA_VERSION,
)


class RuntimeHost:
    """Top-level composition root for runtime engine and scheduler."""

    def __init__(
        self,
        *,
        engine: RuntimeEngine,
        scheduler: RuntimeScheduler,
        wall_clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.engine = engine
        self.scheduler = scheduler
        self._wall_clock = wall_clock or (
            lambda: datetime.now(timezone.utc)
        )

    @property
    def running(self) -> bool:
        return self.scheduler.running

    def start_background(self) -> None:
        self.scheduler.start_background()

    def stop(self) -> None:
        self.scheduler.stop_background()

    def join(self, timeout: float | None = None) -> None:
        self.scheduler.join(timeout=timeout)

    def snapshot(self) -> HostSnapshot:
        background_error = self.scheduler.last_background_error

        capability_snapshots: dict[str, Any] = {}

        list_instances = getattr(
            self.engine,
            "list_instances",
            None,
        )

        instances = (
            list_instances()
            if callable(list_instances)
            else ()
        )

        for session_id, instance in instances:
            snapshot_method = getattr(instance, "snapshot", None)

            if not callable(snapshot_method):
                continue

            try:
                capability_snapshots[session_id] = snapshot_method()
            except Exception as exc:
                capability_snapshots[session_id] = {
                    "status": "error",
                    "error": str(exc),
                }

        generated_at = self._wall_clock()

        if generated_at.tzinfo is None:
            generated_at = generated_at.replace(
                tzinfo=timezone.utc
            )

        return {
            "schemaVersion": SNAPSHOT_SCHEMA_VERSION,
            "generatedAt": generated_at.isoformat(),
            "runtime": self.engine.snapshot(),
            "scheduler": {
                "running": self.scheduler.running,
                "backgroundRunning": (
                    self.scheduler.background_running
                ),
                "backgroundFailed": (
                    self.scheduler.background_failed
                ),
                "lastBackgroundError": (
                    str(background_error)
                    if background_error is not None
                    else None
                ),
                "intervalSeconds": (
                    self.scheduler.interval_seconds
                ),
                "nextRunAt": self.scheduler.next_run_at,
            },
            "capabilities": capability_snapshots,
        }

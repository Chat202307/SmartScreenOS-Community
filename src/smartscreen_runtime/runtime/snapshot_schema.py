from __future__ import annotations

from typing import Any, TypedDict

SNAPSHOT_SCHEMA_VERSION = "1.0"


class RuntimeInstalledCapabilitySnapshot(TypedDict):
    capabilityId: str
    name: str
    version: str


class RuntimeSessionSnapshot(TypedDict):
    sessionId: str
    capabilityId: str
    state: str
    tickHealth: str | None
    consecutiveFailures: int
    lastError: str | None


class RuntimeSnapshot(TypedDict):
    installed: list[RuntimeInstalledCapabilitySnapshot]
    sessions: list[RuntimeSessionSnapshot]


class SchedulerSnapshot(TypedDict):
    running: bool
    backgroundRunning: bool
    backgroundFailed: bool
    lastBackgroundError: str | None
    intervalSeconds: float
    nextRunAt: float


class HostSnapshot(TypedDict):
    schemaVersion: str
    generatedAt: str
    runtime: RuntimeSnapshot
    scheduler: SchedulerSnapshot
    capabilities: dict[str, Any]

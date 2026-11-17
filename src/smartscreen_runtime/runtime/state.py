from __future__ import annotations

from enum import Enum


class RuntimeState(str, Enum):
    """Lifecycle state of an installed capability or runtime session."""

    INSTALLED = "installed"

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"

    # Retained for compatibility with earlier runtime code.
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNINSTALLED = "uninstalled"

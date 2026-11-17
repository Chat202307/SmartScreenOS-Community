from typing import get_type_hints

from src.smartscreen_runtime.runtime.snapshot_schema import (
    HostSnapshot,
    RuntimeInstalledCapabilitySnapshot,
    RuntimeSessionSnapshot,
    RuntimeSnapshot,
    SchedulerSnapshot,
)


def test_runtime_installed_capability_snapshot_fields():
    hints = get_type_hints(
        RuntimeInstalledCapabilitySnapshot
    )

    assert set(hints) == {
        "capabilityId",
        "name",
        "version",
    }


def test_runtime_session_snapshot_fields():
    hints = get_type_hints(RuntimeSessionSnapshot)

    assert set(hints) == {
        "sessionId",
        "capabilityId",
        "state",
        "tickHealth",
        "consecutiveFailures",
        "lastError",
    }


def test_runtime_snapshot_fields():
    hints = get_type_hints(RuntimeSnapshot)

    assert set(hints) == {
        "installed",
        "sessions",
    }


def test_scheduler_snapshot_fields():
    hints = get_type_hints(SchedulerSnapshot)

    assert set(hints) == {
        "running",
        "backgroundRunning",
        "backgroundFailed",
        "lastBackgroundError",
        "intervalSeconds",
        "nextRunAt",
    }


def test_host_snapshot_fields():
    hints = get_type_hints(HostSnapshot)

    assert set(hints) == {
        "schemaVersion",
        "generatedAt",
        "runtime",
        "scheduler",
        "capabilities",
    }

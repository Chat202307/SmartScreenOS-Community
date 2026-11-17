from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class SuccessfulSnapshotCapability:
    def snapshot(self):
        return {
            "value": 42,
        }


class FailingSnapshotCapability:
    def snapshot(self):
        raise RuntimeError("snapshot unavailable")


class NoSnapshotCapability:
    pass


def create_host():
    engine = RuntimeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=1,
        start_time=100.0,
    )

    return RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )


def test_successful_capability_snapshot_remains_unchanged():
    host = create_host()

    host.engine._instances[
        "session-success"
    ] = SuccessfulSnapshotCapability()

    snapshot = host.snapshot()

    assert snapshot["capabilities"]["session-success"] == {
        "value": 42,
    }


def test_failing_capability_snapshot_is_reported():
    host = create_host()

    host.engine._instances[
        "session-failing"
    ] = FailingSnapshotCapability()

    snapshot = host.snapshot()

    assert snapshot["capabilities"]["session-failing"] == {
        "status": "error",
        "error": "snapshot unavailable",
    }


def test_capability_without_snapshot_is_not_reported():
    host = create_host()

    host.engine._instances[
        "session-no-snapshot"
    ] = NoSnapshotCapability()

    snapshot = host.snapshot()

    assert (
        "session-no-snapshot"
        not in snapshot["capabilities"]
    )


def test_snapshot_failure_does_not_break_other_capabilities():
    host = create_host()

    host.engine._instances[
        "session-success"
    ] = SuccessfulSnapshotCapability()

    host.engine._instances[
        "session-failing"
    ] = FailingSnapshotCapability()

    snapshot = host.snapshot()

    assert snapshot["capabilities"]["session-success"] == {
        "value": 42,
    }

    assert snapshot["capabilities"]["session-failing"] == {
        "status": "error",
        "error": "snapshot unavailable",
    }


def test_snapshot_failure_does_not_break_host_snapshot():
    host = create_host()

    host.engine._instances[
        "session-failing"
    ] = FailingSnapshotCapability()

    snapshot = host.snapshot()

    assert snapshot["schemaVersion"] == "1.0"
    assert "generatedAt" in snapshot
    assert "runtime" in snapshot
    assert "scheduler" in snapshot

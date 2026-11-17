import pytest

from src.smartscreen_runtime.runtime.bootstrap import (
    RuntimeBootstrapError,
    create_runtime_host,
)
from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


def create_host(engine=None):
    engine = engine or RuntimeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=100.0,
        loop_sleep_seconds=0.001,
    )

    return RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )


def test_bootstrap_failure_leaves_existing_engine_clean():
    engine = RuntimeEngine()

    with pytest.raises(RuntimeBootstrapError):
        create_runtime_host(
            engine=engine,
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-clock-main",
                },
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ],
        )

    assert engine.list_instances() == ()
    assert engine.sessions.list() == ()


def test_capability_snapshot_failure_does_not_break_host():
    host = create_host()

    class FailingSnapshotCapability:
        def snapshot(self):
            raise RuntimeError("snapshot failed")

    host.engine._instances[
        "session-failing"
    ] = FailingSnapshotCapability()

    snapshot = host.snapshot()

    assert snapshot["capabilities"]["session-failing"] == {
        "status": "error",
        "error": "snapshot failed",
    }

    assert snapshot["schemaVersion"] == "1.0"
    assert "runtime" in snapshot
    assert "scheduler" in snapshot


def test_background_scheduler_failure_can_be_joined():
    class FailingEngine:
        def tick(self):
            raise RuntimeError("scheduler failed")

        def snapshot(self):
            return {
                "installed": [],
                "sessions": [],
            }

        def list_instances(self):
            return ()

    engine = FailingEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=0.0,
        clock=lambda: 1.0,
        loop_sleep_seconds=0.001,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )

    host.start_background()
    host.join(timeout=1.0)

    assert scheduler.background_failed is True
    assert scheduler.background_running is False
    assert isinstance(
        scheduler.last_background_error,
        RuntimeError,
    )


def test_stop_is_safe_when_host_was_never_started():
    host = create_host()

    host.stop()
    host.join(timeout=1.0)

    assert host.running is False
    assert host.scheduler.background_running is False


def test_stop_can_be_called_more_than_once():
    host = create_host()

    host.start_background()

    host.stop()
    host.stop()

    host.join(timeout=1.0)

    assert host.running is False
    assert host.scheduler.background_running is False


def test_shutdown_removes_running_instances():
    host = create_host()

    capability = host.engine.install(
        "examples/capabilities/clock"
    )

    session = host.engine.start(
        capability.capability_id,
        session_id="session-clock-main",
    )

    assert host.engine.get_instance(
        session.session_id
    ) is not None

    host.engine.stop(session.session_id)

    assert host.engine.list_instances() == ()


def test_snapshot_remains_available_after_scheduler_failure():
    class FailingEngine:
        def tick(self):
            raise RuntimeError("scheduler failed")

        def snapshot(self):
            return {
                "installed": [],
                "sessions": [],
            }

        def list_instances(self):
            return ()

    engine = FailingEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=0.0,
        clock=lambda: 1.0,
        loop_sleep_seconds=0.001,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )

    host.start_background()
    host.join(timeout=1.0)

    snapshot = host.snapshot()

    assert snapshot["scheduler"]["backgroundFailed"] is True
    assert (
        snapshot["scheduler"]["lastBackgroundError"]
        == "scheduler failed"
    )

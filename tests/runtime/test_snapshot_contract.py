import json

from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


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


def test_host_snapshot_has_final_top_level_contract():
    host = create_host()

    snapshot = host.snapshot()

    assert set(snapshot) == {
        "schemaVersion",
        "generatedAt",
        "runtime",
        "scheduler",
        "capabilities",
    }


def test_runtime_snapshot_has_final_contract():
    host = create_host()

    snapshot = host.snapshot()

    assert set(snapshot["runtime"]) == {
        "installed",
        "sessions",
    }


def test_scheduler_snapshot_has_final_contract():
    host = create_host()

    snapshot = host.snapshot()

    assert set(snapshot["scheduler"]) == {
        "running",
        "backgroundRunning",
        "backgroundFailed",
        "lastBackgroundError",
        "intervalSeconds",
        "nextRunAt",
    }


def test_empty_snapshot_is_json_serializable():
    host = create_host()

    encoded = json.dumps(
        host.snapshot(),
        ensure_ascii=False,
    )

    decoded = json.loads(encoded)

    assert decoded["schemaVersion"] == "1.0"


def test_clock_snapshot_is_json_serializable():
    host = create_host()

    capability = host.engine.install(
        "examples/capabilities/clock"
    )

    session = host.engine.start(
        capability.capability_id,
        session_id="session-clock-main",
    )

    encoded = json.dumps(
        host.snapshot(),
        ensure_ascii=False,
    )

    decoded = json.loads(encoded)

    assert "session-clock-main" in decoded["capabilities"]

    host.engine.stop(session.session_id)


def test_capability_snapshot_error_is_json_serializable():
    host = create_host()

    class FailingCapability:
        def snapshot(self):
            raise RuntimeError("snapshot unavailable")

    host.engine._instances[
        "session-failing"
    ] = FailingCapability()

    encoded = json.dumps(
        host.snapshot(),
        ensure_ascii=False,
    )

    decoded = json.loads(encoded)

    assert decoded["capabilities"]["session-failing"] == {
        "status": "error",
        "error": "snapshot unavailable",
    }

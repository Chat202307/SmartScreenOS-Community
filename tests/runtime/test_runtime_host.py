from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class FakeEngine(RuntimeEngine):
    pass


def create_host():
    engine = FakeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )

    return host, engine, scheduler


def test_host_exposes_engine_and_scheduler():
    host, engine, scheduler = create_host()

    assert host.engine is engine
    assert host.scheduler is scheduler


def test_host_snapshot_contains_runtime_snapshot():
    host, engine, scheduler = create_host()

    snapshot = host.snapshot()

    assert snapshot["runtime"] == engine.snapshot()


def test_host_snapshot_contains_scheduler_state():
    host, engine, scheduler = create_host()

    snapshot = host.snapshot()

    assert snapshot["scheduler"] == {
        "running": True,
        "backgroundRunning": False,
        "backgroundFailed": False,
        "lastBackgroundError": None,
        "intervalSeconds": 10.0,
        "nextRunAt": 110.0,
    }


def test_host_snapshot_reports_stopped_scheduler():
    host, engine, scheduler = create_host()

    scheduler.stop()

    snapshot = host.snapshot()

    assert snapshot["scheduler"]["running"] is False
    assert snapshot["scheduler"]["backgroundRunning"] is False


def test_host_snapshot_reports_background_failure():
    class FailingEngine:
        def tick(self):
            raise RuntimeError("runtime scheduler failed")

        def snapshot(self):
            return {
                "installed": [],
                "sessions": [],
            }

    engine = FailingEngine()

    times = iter([110.0])

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
        clock=lambda: next(times),
        loop_sleep_seconds=0.001,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )

    scheduler.start_background()
    scheduler.join(timeout=1.0)

    snapshot = host.snapshot()

    assert snapshot["scheduler"]["backgroundRunning"] is False
    assert snapshot["scheduler"]["backgroundFailed"] is True
    assert (
        snapshot["scheduler"]["lastBackgroundError"]
        == "runtime scheduler failed"
    )

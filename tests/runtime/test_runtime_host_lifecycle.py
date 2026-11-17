import time

from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


def create_host():
    engine = RuntimeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )

    return host, engine, scheduler


def test_host_reports_running_state():
    host, engine, scheduler = create_host()

    assert host.running is True


def test_host_start_background_starts_scheduler():
    host, engine, scheduler = create_host()

    host.start_background()

    assert host.running is True
    assert scheduler.background_running is True

    host.stop()
    host.join(timeout=1.0)


def test_host_stop_stops_scheduler():
    host, engine, scheduler = create_host()

    host.start_background()
    host.stop()
    host.join(timeout=1.0)

    assert host.running is False
    assert scheduler.running is False
    assert scheduler.background_running is False


def test_host_join_is_safe_without_background_thread():
    host, engine, scheduler = create_host()

    host.join(timeout=0.01)

    assert host.running is True


def test_host_can_restart_after_stop():
    host, engine, scheduler = create_host()

    try:
        host.start_background()
        host.stop()
        # A timed join does not promise that the old thread has exited.
        # Establish the restart precondition explicitly on a loaded runner.
        host.join(timeout=10.0)
        assert scheduler.background_running is False
        assert host.running is False

        host.start_background()

        assert host.running is True
        assert scheduler.background_running is True
    finally:
        host.stop()
        host.join(timeout=10.0)


def test_host_snapshot_reflects_lifecycle():
    host, engine, scheduler = create_host()

    host.start_background()

    snapshot = host.snapshot()

    assert snapshot["scheduler"]["running"] is True
    assert snapshot["scheduler"]["backgroundRunning"] is True

    host.stop()
    host.join(timeout=1.0)

    snapshot = host.snapshot()

    assert snapshot["scheduler"]["running"] is False
    assert snapshot["scheduler"]["backgroundRunning"] is False

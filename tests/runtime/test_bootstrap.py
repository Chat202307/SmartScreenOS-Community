from src.smartscreen_runtime.runtime.bootstrap import create_runtime_host
from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


def test_create_runtime_host_returns_host():
    host = create_runtime_host()

    assert isinstance(host, RuntimeHost)


def test_create_runtime_host_builds_engine():
    host = create_runtime_host()

    assert isinstance(host.engine, RuntimeEngine)


def test_create_runtime_host_builds_scheduler():
    host = create_runtime_host()

    assert isinstance(host.scheduler, RuntimeScheduler)


def test_default_scheduler_interval():
    host = create_runtime_host()

    assert host.scheduler.interval_seconds == 1.0


def test_custom_scheduler_interval():
    host = create_runtime_host(
        scheduler_interval_seconds=5.0,
    )

    assert host.scheduler.interval_seconds == 5.0


def test_scheduler_uses_current_start_time():
    times = iter([100.0])

    host = create_runtime_host(
        clock=lambda: next(times),
        scheduler_interval_seconds=10.0,
    )

    assert host.scheduler.next_run_at == 110.0


def test_bootstrap_does_not_start_background_thread():
    host = create_runtime_host()

    assert host.scheduler.background_running is False


def test_invalid_scheduler_interval_is_rejected():
    try:
        create_runtime_host(
            scheduler_interval_seconds=0,
        )
    except ValueError as exc:
        assert "interval" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")

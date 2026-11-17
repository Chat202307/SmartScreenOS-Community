import time

from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class SuccessfulEngine:
    def tick(self):
        return {}


class FailingEngine:
    def __init__(self) -> None:
        self.tick_calls = 0

    def tick(self):
        self.tick_calls += 1
        raise RuntimeError("scheduler tick failed")


def test_background_has_no_error_initially():
    scheduler = RuntimeScheduler(
        SuccessfulEngine(),
        interval_seconds=10,
        start_time=100.0,
    )

    assert scheduler.last_background_error is None
    assert scheduler.background_failed is False


def test_background_records_uncaught_error():
    engine = FailingEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()
    scheduler.join(timeout=1.0)

    assert engine.tick_calls == 1
    assert scheduler.background_running is False
    assert scheduler.background_failed is True
    assert isinstance(
        scheduler.last_background_error,
        RuntimeError,
    )
    assert (
        str(scheduler.last_background_error)
        == "scheduler tick failed"
    )


def test_successful_background_start_clears_previous_error():
    engine = FailingEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()
    scheduler.join(timeout=1.0)

    assert scheduler.background_failed is True

    scheduler._engine = SuccessfulEngine()

    scheduler.start_background()

    assert scheduler.background_failed is False
    assert scheduler.last_background_error is None

    scheduler.stop_background()
    scheduler.join(timeout=1.0)


def test_manual_stop_is_not_background_failure():
    scheduler = RuntimeScheduler(
        SuccessfulEngine(),
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()
    scheduler.stop_background()
    scheduler.join(timeout=1.0)

    assert scheduler.background_running is False
    assert scheduler.background_failed is False
    assert scheduler.last_background_error is None


def test_background_can_restart_after_failure():
    engine = FailingEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()
    scheduler.join(timeout=1.0)

    assert scheduler.background_failed is True

    scheduler._engine = SuccessfulEngine()
    scheduler.start_background()

    assert scheduler.background_running is True
    assert scheduler.background_failed is False

    scheduler.stop_background()
    scheduler.join(timeout=1.0)

    assert scheduler.background_running is False

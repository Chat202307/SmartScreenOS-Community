import threading
import time

from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class FakeEngine:
    def __init__(self) -> None:
        self.tick_calls = 0
        self.lock = threading.Lock()

    def tick(self):
        with self.lock:
            self.tick_calls += 1
            return {"tick": self.tick_calls}


def test_background_not_running_initially():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    assert scheduler.background_running is False


def test_start_background_starts_thread():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()

    assert scheduler.background_running is True

    scheduler.stop_background()
    scheduler.join(timeout=1.0)

    assert scheduler.background_running is False


def test_background_scheduler_ticks_engine():
    engine = FakeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()

    deadline = time.monotonic() + 1.0
    while engine.tick_calls == 0 and time.monotonic() < deadline:
        time.sleep(0.001)

    scheduler.stop_background()
    scheduler.join(timeout=1.0)

    assert engine.tick_calls >= 1


def test_start_background_is_idempotent():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()
    first_thread = scheduler._background_thread

    scheduler.start_background()
    second_thread = scheduler._background_thread

    assert first_thread is second_thread

    scheduler.stop_background()
    scheduler.join(timeout=1.0)


def test_stop_background_is_safe_when_not_started():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.stop_background()
    scheduler.join(timeout=0.01)

    assert scheduler.background_running is False


def test_join_returns_after_background_stop():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=0.01,
        start_time=time.monotonic(),
        loop_sleep_seconds=0.001,
    )

    scheduler.start_background()
    scheduler.stop_background()
    scheduler.join(timeout=1.0)

    assert scheduler.background_running is False

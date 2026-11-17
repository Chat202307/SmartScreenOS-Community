from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class FakeEngine:
    def __init__(self) -> None:
        self.tick_calls = 0

    def tick(self):
        self.tick_calls += 1
        return {"tick": self.tick_calls}


def test_scheduler_starts_running_by_default():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=10,
        start_time=100.0,
    )

    assert scheduler.running is True


def test_stop_prevents_ticks():
    engine = FakeEngine()
    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    scheduler.stop()

    result = scheduler.poll(now=110.0)

    assert result is None
    assert engine.tick_calls == 0
    assert scheduler.running is False


def test_start_resumes_scheduler_from_new_time():
    engine = FakeEngine()
    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    scheduler.stop()
    scheduler.start(now=200.0)

    assert scheduler.running is True
    assert scheduler.next_run_at == 210.0

    assert scheduler.poll(now=209.9) is None
    assert scheduler.poll(now=210.0) == {"tick": 1}


def test_start_is_idempotent_when_already_running():
    scheduler = RuntimeScheduler(
        FakeEngine(),
        interval_seconds=10,
        start_time=100.0,
    )

    original_next_run_at = scheduler.next_run_at

    scheduler.start(now=200.0)

    assert scheduler.next_run_at == original_next_run_at


def test_reset_reschedules_running_scheduler():
    engine = FakeEngine()
    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    scheduler.reset(now=150.0)

    assert scheduler.running is True
    assert scheduler.next_run_at == 160.0
    assert scheduler.poll(now=159.9) is None
    assert scheduler.poll(now=160.0) == {"tick": 1}


def test_reset_preserves_stopped_state():
    engine = FakeEngine()
    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    scheduler.stop()
    scheduler.reset(now=150.0)

    assert scheduler.running is False
    assert scheduler.next_run_at == 160.0
    assert scheduler.poll(now=160.0) is None
    assert engine.tick_calls == 0

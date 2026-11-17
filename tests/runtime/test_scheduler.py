from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class FakeEngine:
    def __init__(self) -> None:
        self.tick_calls = 0

    def tick(self):
        self.tick_calls += 1
        return {}


def test_scheduler_does_not_tick_before_interval():
    engine = FakeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    result = scheduler.poll(now=109.9)

    assert result is None
    assert engine.tick_calls == 0


def test_scheduler_ticks_at_interval_boundary():
    engine = FakeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    result = scheduler.poll(now=110.0)

    assert result == {}
    assert engine.tick_calls == 1


def test_scheduler_reschedules_after_tick():
    engine = FakeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    scheduler.poll(now=110.0)
    scheduler.poll(now=119.9)

    assert engine.tick_calls == 1

    scheduler.poll(now=120.0)

    assert engine.tick_calls == 2


def test_scheduler_does_not_catch_up_missed_ticks():
    engine = FakeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    scheduler.poll(now=135.0)

    assert engine.tick_calls == 1

    scheduler.poll(now=144.9)

    assert engine.tick_calls == 1

    scheduler.poll(now=145.0)

    assert engine.tick_calls == 2


def test_scheduler_rejects_zero_interval():
    try:
        RuntimeScheduler(
            FakeEngine(),
            interval_seconds=0,
            start_time=100.0,
        )
    except ValueError as exc:
        assert "interval" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_scheduler_rejects_negative_interval():
    try:
        RuntimeScheduler(
            FakeEngine(),
            interval_seconds=-1,
            start_time=100.0,
        )
    except ValueError as exc:
        assert "interval" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")

from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class FakeEngine:
    def __init__(self) -> None:
        self.tick_calls = 0

    def tick(self):
        self.tick_calls += 1
        return {"tick": self.tick_calls}


class FakeClock:
    def __init__(self, values):
        self._values = iter(values)

    def __call__(self):
        return next(self._values)


def test_run_once_polls_using_injected_clock():
    engine = FakeEngine()
    clock = FakeClock([110.0])

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
        clock=clock,
    )

    result = scheduler.run_once()

    assert result == {"tick": 1}
    assert engine.tick_calls == 1


def test_run_once_does_not_tick_before_due_time():
    engine = FakeEngine()
    clock = FakeClock([109.0])

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
        clock=clock,
    )

    result = scheduler.run_once()

    assert result is None
    assert engine.tick_calls == 0


def test_run_executes_until_stopped():
    engine = FakeEngine()

    times = iter([
        109.0,
        110.0,
        119.0,
        120.0,
    ])

    sleep_calls = []

    scheduler = None

    def clock():
        return next(times)

    def sleep(seconds):
        sleep_calls.append(seconds)

        if len(sleep_calls) == 4:
            scheduler.stop()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
        clock=clock,
        sleep=sleep,
        loop_sleep_seconds=0.5,
    )

    scheduler.run()

    assert engine.tick_calls == 2
    assert sleep_calls == [0.5, 0.5, 0.5, 0.5]
    assert scheduler.running is False


def test_run_returns_immediately_when_stopped():
    engine = FakeEngine()

    clock_calls = 0
    sleep_calls = 0

    def clock():
        nonlocal clock_calls
        clock_calls += 1
        return 110.0

    def sleep(seconds):
        nonlocal sleep_calls
        sleep_calls += 1

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
        clock=clock,
        sleep=sleep,
    )

    scheduler.stop()
    scheduler.run()

    assert clock_calls == 0
    assert sleep_calls == 0
    assert engine.tick_calls == 0


def test_loop_sleep_interval_must_be_positive():
    try:
        RuntimeScheduler(
            FakeEngine(),
            interval_seconds=10,
            start_time=100.0,
            loop_sleep_seconds=0,
        )
    except ValueError as exc:
        assert "sleep" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")

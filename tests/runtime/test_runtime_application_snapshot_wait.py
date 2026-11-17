from src.smartscreen_runtime.runtime import application


class FakeScheduler:
    def __init__(self) -> None:
        self.background_failed = False
        self.last_background_error = None


class FakeEngine:
    def __init__(self) -> None:
        self.health_ready = False

    def get_tick_health_summary(self):
        if self.health_ready:
            return {
                "session-weather-main": object(),
            }

        return {}


class FakeHost:
    def __init__(self) -> None:
        self.scheduler = FakeScheduler()
        self.engine = FakeEngine()
        self.started = False
        self.stopped = False
        self.joined = False

    def start_background(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout=None) -> None:
        self.joined = True

    def snapshot(self):
        return {
            "runtime": {
                "installed": [],
                "sessions": [],
            },
            "scheduler": {
                "running": True,
                "backgroundRunning": True,
                "backgroundFailed": False,
                "lastBackgroundError": None,
                "intervalSeconds": 1.0,
                "nextRunAt": 110.0,
            },
        }


def test_snapshot_waits_until_tick_health_is_ready():
    host = FakeHost()
    wait_calls = 0

    def host_factory(path):
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1

        if wait_calls == 3:
            host.engine.health_ready = True

    result = application.run_snapshot(
        host_factory=host_factory,
        wait=wait,
        timeout_seconds=15.0,
    )

    assert result == 0
    assert wait_calls == 3


def test_snapshot_returns_immediately_when_health_is_ready():
    host = FakeHost()
    host.engine.health_ready = True

    wait_calls = 0

    def host_factory(path):
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1

    result = application.run_snapshot(
        host_factory=host_factory,
        wait=wait,
        timeout_seconds=15.0,
    )

    assert result == 0
    assert wait_calls == 0


def test_snapshot_stops_waiting_at_timeout():
    host = FakeHost()

    times = iter([
        100.0,
        101.0,
        102.0,
        103.0,
        104.0,
        105.0,
    ])

    wait_calls = 0

    def host_factory(path):
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1

    result = application.run_snapshot(
        host_factory=host_factory,
        wait=wait,
        timeout_seconds=5.0,
        clock=lambda: next(times),
    )

    assert result == 0
    assert wait_calls > 0


def test_snapshot_background_failure_interrupts_wait(capsys):
    host = FakeHost()
    wait_calls = 0

    def host_factory(path):
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1

        host.scheduler.background_failed = True
        host.scheduler.last_background_error = RuntimeError(
            "snapshot scheduler crashed"
        )

    result = application.run_snapshot(
        host_factory=host_factory,
        wait=wait,
        timeout_seconds=15.0,
    )

    captured = capsys.readouterr()

    assert result == 1
    assert wait_calls == 1
    assert "snapshot scheduler crashed" in captured.err

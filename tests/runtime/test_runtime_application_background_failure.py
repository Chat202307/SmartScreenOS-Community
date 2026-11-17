from src.smartscreen_runtime.runtime.application import run_runtime


class FakeScheduler:
    def __init__(self) -> None:
        self.background_failed = False
        self.last_background_error = None


class FakeHost:
    def __init__(self) -> None:
        self.scheduler = FakeScheduler()
        self.started = False
        self.stopped = False
        self.joined = False

    def start_background(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout=None) -> None:
        self.joined = True


def test_runtime_returns_one_when_background_scheduler_fails(capsys):
    host = FakeHost()
    wait_calls = 0

    def host_factory(path):
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1

        host.scheduler.background_failed = True
        host.scheduler.last_background_error = RuntimeError(
            "background scheduler failed"
        )

    result = run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    captured = capsys.readouterr()

    assert result == 1
    assert wait_calls == 1
    assert (
        "SmartScreenOS Runtime background scheduler failed:"
        in captured.err
    )
    assert "background scheduler failed" in captured.err
    assert host.stopped is True
    assert host.joined is True


def test_background_failure_is_checked_after_wait(capsys):
    host = FakeHost()
    wait_calls = 0

    def host_factory(path):
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1

        if wait_calls == 2:
            host.scheduler.background_failed = True
            host.scheduler.last_background_error = RuntimeError(
                "tick loop crashed"
            )

    result = run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    assert result == 1
    assert wait_calls == 2


def test_clean_interrupt_still_returns_zero():
    host = FakeHost()

    def host_factory(path):
        return host

    def wait():
        raise KeyboardInterrupt

    result = run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    assert result == 0


def test_background_failure_without_error_object_is_reported(capsys):
    host = FakeHost()

    def host_factory(path):
        return host

    def wait():
        host.scheduler.background_failed = True
        host.scheduler.last_background_error = None

    result = run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    captured = capsys.readouterr()

    assert result == 1
    assert "unknown background scheduler error" in captured.err

from pathlib import Path

from src.smartscreen_runtime.runtime.application import (
    run_runtime,
)


class FakeHost:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.joined = False

    def start_background(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout=None) -> None:
        self.joined = True


def test_run_runtime_reports_startup_and_shutdown(capsys):
    host = FakeHost()

    def host_factory(path):
        assert path == Path("config/runtime.yaml")
        return host

    def wait():
        raise KeyboardInterrupt

    result = run_runtime(
        config_path=Path("config/runtime.yaml"),
        host_factory=host_factory,
        wait=wait,
    )

    captured = capsys.readouterr()

    assert result == 0
    assert "SmartScreenOS Runtime starting..." in captured.out
    assert "Config: config/runtime.yaml" in captured.out
    assert "Runtime started." in captured.out
    assert "Press Ctrl+C to stop." in captured.out
    assert "SmartScreenOS Runtime stopping..." in captured.out
    assert "SmartScreenOS Runtime stopped." in captured.out


def test_startup_message_uses_custom_config_path(capsys):
    host = FakeHost()

    def host_factory(path):
        return host

    def wait():
        raise KeyboardInterrupt

    run_runtime(
        config_path=Path("config/custom-runtime.yaml"),
        host_factory=host_factory,
        wait=wait,
    )

    captured = capsys.readouterr()

    assert "Config: config/custom-runtime.yaml" in captured.out


def test_shutdown_messages_are_emitted_after_interrupt(capsys):
    host = FakeHost()

    def host_factory(path):
        return host

    def wait():
        raise KeyboardInterrupt

    run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    captured = capsys.readouterr()

    stopping = captured.out.index(
        "SmartScreenOS Runtime stopping..."
    )
    stopped = captured.out.index(
        "SmartScreenOS Runtime stopped."
    )

    assert stopping < stopped
    assert host.stopped is True
    assert host.joined is True

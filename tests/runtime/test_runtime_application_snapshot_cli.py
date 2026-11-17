import json
from pathlib import Path

from src.smartscreen_runtime.runtime import application


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
        self.snapshot_calls = 0

    def start_background(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def join(self, timeout=None) -> None:
        self.joined = True

    def snapshot(self):
        self.snapshot_calls += 1
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


def test_main_accepts_snapshot_flag(monkeypatch):
    captured = {}

    def fake_run_snapshot(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_snapshot",
        fake_run_snapshot,
    )

    result = application.main(["--snapshot"])

    assert result == 0
    assert captured["config_path"] == Path("config/runtime.yaml")


def test_snapshot_mode_accepts_custom_config(monkeypatch):
    captured = {}

    def fake_run_snapshot(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_snapshot",
        fake_run_snapshot,
    )

    result = application.main(
        [
            "--snapshot",
            "--config",
            "config/custom-runtime.yaml",
        ]
    )

    assert result == 0
    assert (
        captured["config_path"]
        == Path("config/custom-runtime.yaml")
    )


def test_run_snapshot_prints_json(capsys):
    host = FakeHost()

    def host_factory(path):
        return host

    result = application.run_snapshot(
        config_path=Path("config/runtime.yaml"),
        host_factory=host_factory,
        wait=lambda: None,
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert result == 0
    assert payload["runtime"]["installed"] == []
    assert payload["scheduler"]["backgroundFailed"] is False

    assert host.started is True
    assert host.stopped is True
    assert host.joined is True
    assert host.snapshot_calls == 1


def test_run_snapshot_returns_one_on_background_failure(capsys):
    host = FakeHost()

    def host_factory(path):
        return host

    def wait():
        host.scheduler.background_failed = True
        host.scheduler.last_background_error = RuntimeError(
            "snapshot scheduler failed"
        )

    result = application.run_snapshot(
        host_factory=host_factory,
        wait=wait,
    )

    captured = capsys.readouterr()

    assert result == 1
    assert "snapshot scheduler failed" in captured.err
    assert host.stopped is True
    assert host.joined is True


def test_run_snapshot_reports_startup_failure(capsys):
    def failing_host_factory(path):
        raise RuntimeError("snapshot startup failed")

    result = application.run_snapshot(
        host_factory=failing_host_factory,
    )

    captured = capsys.readouterr()

    assert result == 1
    assert "snapshot startup failed" in captured.err

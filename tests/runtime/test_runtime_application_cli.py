from pathlib import Path

from src.smartscreen_runtime.runtime import application


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


def test_main_uses_default_config(monkeypatch):
    host = FakeHost()
    captured = {}

    def fake_run_runtime(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_runtime",
        fake_run_runtime,
    )

    result = application.main([])

    assert result == 0
    assert (
        captured["config_path"]
        == Path("config/runtime.yaml")
    )


def test_main_accepts_custom_config(monkeypatch):
    captured = {}

    def fake_run_runtime(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(
        application,
        "run_runtime",
        fake_run_runtime,
    )

    result = application.main(
        [
            "--config",
            "config/custom-runtime.yaml",
        ]
    )

    assert result == 0
    assert (
        captured["config_path"]
        == Path("config/custom-runtime.yaml")
    )


def test_main_rejects_unknown_argument():
    try:
        application.main(["--unknown"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected SystemExit")


def test_module_exposes_main():
    assert callable(application.main)

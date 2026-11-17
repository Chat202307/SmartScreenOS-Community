from pathlib import Path

from src.smartscreen_runtime.runtime import application


def test_run_runtime_reports_startup_failure(capsys):
    def failing_host_factory(path):
        raise RuntimeError("startup failed")

    result = application.run_runtime(
        config_path=Path("config/runtime.yaml"),
        host_factory=failing_host_factory,
    )

    captured = capsys.readouterr()

    assert result == 1
    assert "SmartScreenOS Runtime failed to start:" in captured.err
    assert "startup failed" in captured.err


def test_run_runtime_does_not_print_started_on_failure(capsys):
    def failing_host_factory(path):
        raise RuntimeError("startup failed")

    application.run_runtime(
        host_factory=failing_host_factory,
    )

    captured = capsys.readouterr()

    assert "Runtime started." not in captured.out


def test_main_returns_nonzero_when_config_missing(tmp_path, capsys):
    missing = tmp_path / "missing.yaml"

    result = application.main(
        [
            "--config",
            str(missing),
        ]
    )

    captured = capsys.readouterr()

    assert result == 1
    assert "failed to start" in captured.err.lower()
    assert "not found" in captured.err.lower()


def test_main_returns_zero_on_clean_interrupt(monkeypatch):
    def fake_run_runtime(**kwargs):
        return 0

    monkeypatch.setattr(
        application,
        "run_runtime",
        fake_run_runtime,
    )

    assert application.main([]) == 0

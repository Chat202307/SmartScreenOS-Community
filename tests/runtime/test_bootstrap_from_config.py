from pathlib import Path

from src.smartscreen_runtime.runtime.bootstrap import (
    create_runtime_host_from_config,
)
from src.smartscreen_runtime.runtime.state import RuntimeState


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "runtime.yaml"
    path.write_text(content)
    return path


def test_create_host_from_empty_config(tmp_path: Path):
    path = write_config(
        tmp_path,
        """
capabilities: []
""",
    )

    host = create_runtime_host_from_config(path)

    assert host.engine.installed() == ()
    assert host.engine.sessions.list() == ()


def test_create_host_from_config_uses_scheduler_interval(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
scheduler:
  intervalSeconds: 5

capabilities: []
""",
    )

    host = create_runtime_host_from_config(path)

    assert host.scheduler.interval_seconds == 5.0


def test_create_host_from_config_bootstraps_clock(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
capabilities:
  - path: examples/capabilities/clock
    sessionId: session-clock-main
    configuration:
      timezone: UTC
      timeFormat: 12h
""",
    )

    host = create_runtime_host_from_config(path)

    session = host.engine.sessions.get(
        "session-clock-main"
    )

    instance = host.engine.get_instance(
        "session-clock-main"
    )

    assert session.state is RuntimeState.RUNNING
    assert instance.context.configuration["timezone"] == "UTC"
    assert instance.context.configuration["timeFormat"] == "12h"


def test_create_host_from_config_bootstraps_multiple_capabilities(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
capabilities:
  - path: examples/capabilities/clock
    sessionId: session-clock-main

  - path: examples/capabilities/weather
    sessionId: session-weather-main
    configuration:
      location: Dalian
""",
    )

    host = create_runtime_host_from_config(path)

    assert len(host.engine.installed()) == 2

    assert (
        host.engine.sessions.get(
            "session-clock-main"
        ).state
        is RuntimeState.RUNNING
    )

    assert (
        host.engine.sessions.get(
            "session-weather-main"
        ).state
        is RuntimeState.RUNNING
    )


def test_create_host_from_config_does_not_start_background(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
capabilities: []
""",
    )

    host = create_runtime_host_from_config(path)

    assert host.scheduler.background_running is False

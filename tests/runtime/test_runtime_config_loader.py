from pathlib import Path

import pytest

from src.smartscreen_runtime.runtime.runtime_config import (
    RuntimeConfigError,
    RuntimeConfigLoader,
)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "runtime.yaml"
    path.write_text(content)
    return path


def test_load_runtime_configuration(tmp_path: Path):
    path = write_config(
        tmp_path,
        """
scheduler:
  intervalSeconds: 1

capabilities:
  - path: examples/capabilities/clock
    sessionId: session-clock-main
    configuration:
      timezone: Asia/Shanghai
      timeFormat: 24h

  - path: examples/capabilities/weather
    sessionId: session-weather-main
    configuration:
      location: "101010100"
      provider: qweather
      language: zh
""",
    )

    config = RuntimeConfigLoader().load(path)

    assert config.scheduler_interval_seconds == 1.0
    assert len(config.capabilities) == 2

    clock = config.capabilities[0]

    assert clock.path == "examples/capabilities/clock"
    assert clock.session_id == "session-clock-main"
    assert clock.configuration == {
        "timezone": "Asia/Shanghai",
        "timeFormat": "24h",
    }


def test_scheduler_interval_defaults_to_one_second(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
capabilities: []
""",
    )

    config = RuntimeConfigLoader().load(path)

    assert config.scheduler_interval_seconds == 1.0


def test_missing_capabilities_defaults_to_empty(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
scheduler:
  intervalSeconds: 5
""",
    )

    config = RuntimeConfigLoader().load(path)

    assert config.capabilities == ()


def test_missing_config_file_is_rejected(tmp_path: Path):
    path = tmp_path / "missing.yaml"

    with pytest.raises(RuntimeConfigError, match="not found"):
        RuntimeConfigLoader().load(path)


def test_invalid_yaml_is_rejected(tmp_path: Path):
    path = write_config(
        tmp_path,
        """
scheduler:
  intervalSeconds: [
""",
    )

    with pytest.raises(RuntimeConfigError, match="yaml"):
        RuntimeConfigLoader().load(path)


def test_invalid_scheduler_interval_is_rejected(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
scheduler:
  intervalSeconds: 0
capabilities: []
""",
    )

    with pytest.raises(RuntimeConfigError, match="interval"):
        RuntimeConfigLoader().load(path)


def test_capability_requires_path(tmp_path: Path):
    path = write_config(
        tmp_path,
        """
capabilities:
  - sessionId: session-clock-main
""",
    )

    with pytest.raises(RuntimeConfigError, match="path"):
        RuntimeConfigLoader().load(path)


def test_capability_requires_session_id(tmp_path: Path):
    path = write_config(
        tmp_path,
        """
capabilities:
  - path: examples/capabilities/clock
""",
    )

    with pytest.raises(RuntimeConfigError, match="session"):
        RuntimeConfigLoader().load(path)


def test_configuration_must_be_mapping(tmp_path: Path):
    path = write_config(
        tmp_path,
        """
capabilities:
  - path: examples/capabilities/clock
    sessionId: session-clock-main
    configuration: invalid
""",
    )

    with pytest.raises(RuntimeConfigError, match="configuration"):
        RuntimeConfigLoader().load(path)


def test_duplicate_session_ids_are_rejected(
    tmp_path: Path,
):
    path = write_config(
        tmp_path,
        """
capabilities:
  - path: examples/capabilities/clock
    sessionId: session-main

  - path: examples/capabilities/weather
    sessionId: session-main
    configuration:
      location: Dalian
""",
    )

    with pytest.raises(RuntimeConfigError, match="duplicate"):
        RuntimeConfigLoader().load(path)

from pathlib import Path

from src.smartscreen_runtime.runtime.application import (
    DEFAULT_CONFIG_PATH,
    run_runtime,
)
from src.smartscreen_runtime.runtime.runtime_config import (
    RuntimeConfigLoader,
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


def test_default_config_path():
    assert DEFAULT_CONFIG_PATH == Path("config/runtime.yaml")


def test_project_runtime_yaml_exists():
    assert DEFAULT_CONFIG_PATH.is_file()


def test_project_runtime_yaml_loads():
    config = RuntimeConfigLoader().load(DEFAULT_CONFIG_PATH)

    assert config.scheduler_interval_seconds > 0
    assert len(config.capabilities) == 1


def test_project_runtime_yaml_contains_clock():
    config = RuntimeConfigLoader().load(DEFAULT_CONFIG_PATH)

    capability_ids = {
        item.session_id
        for item in config.capabilities
    }

    assert "session-clock-main" in capability_ids


def test_example_runtime_yaml_contains_weather():
    config = RuntimeConfigLoader().load(Path("config/runtime.test.yaml"))

    weather = next(
        item
        for item in config.capabilities
        if item.session_id == "session-weather-main"
    )

    assert weather.configuration["location"] == "101010100"
    assert weather.configuration.get("provider", "qweather") == "qweather"
    assert weather.configuration["refreshIntervalSeconds"] == 900


def test_run_runtime_starts_and_stops_host():
    host = FakeHost()
    wait_calls = 0

    def host_factory(path):
        assert path == DEFAULT_CONFIG_PATH
        return host

    def wait():
        nonlocal wait_calls
        wait_calls += 1
        raise KeyboardInterrupt

    result = run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    assert result == 0
    assert wait_calls == 1
    assert host.started is True
    assert host.stopped is True
    assert host.joined is True


def test_run_runtime_cleans_up_on_keyboard_interrupt():
    host = FakeHost()

    def host_factory(path):
        return host

    def wait():
        raise KeyboardInterrupt

    run_runtime(
        host_factory=host_factory,
        wait=wait,
    )

    assert host.stopped is True
    assert host.joined is True

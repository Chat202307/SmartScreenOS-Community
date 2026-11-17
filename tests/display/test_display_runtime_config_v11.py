from pathlib import Path

from src.smartscreen_runtime.runtime.bootstrap import (
    create_runtime_host_from_config,
)


DISPLAY_RUNTIME_CONFIG = Path(
    "config/runtime.display.yaml"
)


def test_display_runtime_config_exists():
    assert DISPLAY_RUNTIME_CONFIG.exists()


def test_display_runtime_config_bootstraps_clock_only():
    host = create_runtime_host_from_config(
        DISPLAY_RUNTIME_CONFIG
    )

    try:
        installed = {
            capability.capability_id
            for capability in host.engine.installed()
        }

        assert installed == {
            "com.smartscreen.capability.clock",
        }

        sessions = {
            session.session_id:
            session.state.value
            for session in host.engine.sessions.list()
        }

        assert sessions == {
            "session-clock-main": "running",
        }

        snapshot = host.snapshot()

        assert (
            "session-clock-main"
            in snapshot["capabilities"]
        )

        assert (
            "session-weather-main"
            not in snapshot["capabilities"]
        )

    finally:
        for session in host.engine.sessions.list():
            if session.state.value == "running":
                host.engine.stop(
                    session.session_id
                )

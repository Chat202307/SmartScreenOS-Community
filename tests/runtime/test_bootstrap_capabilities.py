from src.smartscreen_runtime.runtime.bootstrap import create_runtime_host
from src.smartscreen_runtime.runtime.state import RuntimeState


def test_bootstrap_installs_capability():
    host = create_runtime_host(
        capabilities=[
            {
                "path": "examples/capabilities/clock",
                "session_id": "session-clock-main",
            }
        ]
    )

    installed = host.engine.installed()

    assert len(installed) == 1
    assert (
        installed[0].capability_id
        == "com.smartscreen.capability.clock"
    )


def test_bootstrap_starts_capability_session():
    host = create_runtime_host(
        capabilities=[
            {
                "path": "examples/capabilities/clock",
                "session_id": "session-clock-main",
            }
        ]
    )

    session = host.engine.sessions.get(
        "session-clock-main"
    )

    assert session.state is RuntimeState.RUNNING
    assert (
        session.capability_id
        == "com.smartscreen.capability.clock"
    )


def test_bootstrap_passes_runtime_configuration():
    host = create_runtime_host(
        capabilities=[
            {
                "path": "examples/capabilities/clock",
                "session_id": "session-clock-main",
                "configuration": {
                    "timezone": "UTC",
                    "timeFormat": "12h",
                },
            }
        ]
    )

    instance = host.engine.get_instance(
        "session-clock-main"
    )

    assert instance.context.configuration["timezone"] == "UTC"
    assert instance.context.configuration["timeFormat"] == "12h"


def test_bootstrap_supports_multiple_capabilities():
    host = create_runtime_host(
        capabilities=[
            {
                "path": "examples/capabilities/clock",
                "session_id": "session-clock-main",
            },
            {
                "path": "examples/capabilities/weather",
                "session_id": "session-weather-main",
                "configuration": {
                    "location": "Dalian",
                },
            },
        ]
    )

    assert len(host.engine.installed()) == 2

    clock_session = host.engine.sessions.get(
        "session-clock-main"
    )
    weather_session = host.engine.sessions.get(
        "session-weather-main"
    )

    assert clock_session.state is RuntimeState.RUNNING
    assert weather_session.state is RuntimeState.RUNNING


def test_bootstrap_without_capabilities_remains_empty():
    host = create_runtime_host()

    assert host.engine.installed() == ()
    assert host.engine.sessions.list() == ()


def test_bootstrap_does_not_start_background_scheduler():
    host = create_runtime_host(
        capabilities=[
            {
                "path": "examples/capabilities/clock",
                "session_id": "session-clock-main",
            }
        ]
    )

    assert host.scheduler.background_running is False

import pytest

from src.smartscreen_runtime.runtime.bootstrap import (
    RuntimeBootstrapError,
    create_runtime_host,
)
from src.smartscreen_runtime.runtime.engine import RuntimeEngine


def test_bootstrap_accepts_existing_engine():
    engine = RuntimeEngine()

    host = create_runtime_host(engine=engine)

    assert host.engine is engine


def test_failed_bootstrap_removes_all_installed_capabilities():
    engine = RuntimeEngine()

    with pytest.raises(RuntimeBootstrapError):
        create_runtime_host(
            engine=engine,
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-clock-main",
                },
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ],
        )

    assert engine.installed() == ()


def test_failed_bootstrap_removes_created_sessions():
    engine = RuntimeEngine()

    with pytest.raises(RuntimeBootstrapError):
        create_runtime_host(
            engine=engine,
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-clock-main",
                },
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ],
        )

    assert engine.sessions.list() == ()


def test_failed_bootstrap_removes_running_instances():
    engine = RuntimeEngine()

    with pytest.raises(RuntimeBootstrapError):
        create_runtime_host(
            engine=engine,
            capabilities=[
                {
                    "path": "examples/capabilities/clock",
                    "session_id": "session-clock-main",
                },
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ],
        )

    assert engine._instances == {}


def test_rollback_does_not_remove_preexisting_capability():
    engine = RuntimeEngine()

    preexisting = engine.install(
        "examples/capabilities/clock"
    )

    with pytest.raises(RuntimeBootstrapError):
        create_runtime_host(
            engine=engine,
            capabilities=[
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ],
        )

    assert engine.installed() == (preexisting,)
    assert (
        engine.registry.get(preexisting.capability_id)
        is preexisting
    )


def test_atomic_rollback_preserves_original_cause():
    engine = RuntimeEngine()

    with pytest.raises(RuntimeBootstrapError) as exc_info:
        create_runtime_host(
            engine=engine,
            capabilities=[
                {
                    "path": "examples/capabilities/weather",
                    "session_id": "session-weather-main",
                    "configuration": {
                        "location": "",
                    },
                },
            ],
        )

    assert exc_info.value.__cause__ is not None

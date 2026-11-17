import pytest

from src.smartscreen_runtime.runtime.capability_registry import (
    CapabilityNotRegisteredError,
)
from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.session_manager import (
    CapabilitySessionNotFoundError,
)
from src.smartscreen_runtime.runtime.state import RuntimeState


def install_clock(engine: RuntimeEngine):
    return engine.install("examples/capabilities/clock")


def test_start_capability_creates_running_session():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    assert session.session_id == "session-clock-001"
    assert session.capability_id == capability.capability_id
    assert session.state is RuntimeState.RUNNING
    assert engine.sessions.get(session.session_id) == session


def test_start_unknown_capability_is_rejected():
    engine = RuntimeEngine()

    with pytest.raises(CapabilityNotRegisteredError):
        engine.start(
            "unknown-capability",
            session_id="session-unknown-001",
        )


def test_stop_running_session():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    stopped = engine.stop(session.session_id)

    assert stopped is session
    assert stopped.state is RuntimeState.STOPPED
    assert engine.sessions.get(session.session_id) is session


def test_stop_unknown_session_is_rejected():
    engine = RuntimeEngine()

    with pytest.raises(CapabilitySessionNotFoundError):
        engine.stop("unknown-session")


def test_session_manager_updates_state():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.sessions.create(
        session_id="session-clock-001",
        manifest=capability.manifest,
        state=RuntimeState.INSTALLED,
    )

    updated = engine.sessions.update_state(
        session.session_id,
        RuntimeState.RUNNING,
    )

    assert updated is session
    assert session.state is RuntimeState.RUNNING


def test_runtime_states_have_lifecycle_values():
    assert RuntimeState.STARTING.value == "starting"
    assert RuntimeState.RUNNING.value == "running"
    assert RuntimeState.STOPPING.value == "stopping"
    assert RuntimeState.STOPPED.value == "stopped"
    assert RuntimeState.FAILED.value == "failed"

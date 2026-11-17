import pytest

from src.smartscreen_runtime.runtime.engine import (
    CapabilityHasActiveSessionsError,
    RuntimeEngine,
)
from src.smartscreen_runtime.runtime.state import RuntimeState


def install_clock(engine: RuntimeEngine):
    return engine.install("examples/capabilities/clock")


def test_uninstall_running_capability_is_rejected():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    with pytest.raises(CapabilityHasActiveSessionsError):
        engine.uninstall(capability.capability_id)

    assert engine.registry.get(capability.capability_id) == capability
    assert session.state is RuntimeState.RUNNING


def test_uninstall_stopped_capability_is_allowed():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )
    engine.stop(session.session_id)

    removed = engine.uninstall(capability.capability_id)

    assert removed == capability
    assert engine.installed() == ()


def test_session_manager_lists_sessions_by_capability():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    first = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )
    second = engine.start(
        capability.capability_id,
        session_id="session-clock-002",
    )

    assert engine.sessions.list_by_capability(
        capability.capability_id
    ) == (first, second)


def test_session_manager_lists_active_sessions_by_capability():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    first = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )
    second = engine.start(
        capability.capability_id,
        session_id="session-clock-002",
    )

    engine.stop(first.session_id)

    assert engine.sessions.list_active_by_capability(
        capability.capability_id
    ) == (second,)

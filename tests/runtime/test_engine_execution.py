import pytest

from src.smartscreen_runtime.runtime.capability_factory import CapabilityFactory
from src.smartscreen_runtime.runtime.engine import (
    CapabilityInstanceNotFoundError,
    RuntimeEngine,
)
from src.smartscreen_runtime.runtime.state import RuntimeState


def install_clock(engine: RuntimeEngine):
    return engine.install("examples/capabilities/clock")


def test_start_creates_and_starts_capability_instance():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    instance = engine.get_instance(session.session_id)

    assert instance.__class__.__name__ == "ClockCapability"
    assert instance.started is True
    assert session.state is RuntimeState.RUNNING


def test_stop_stops_and_removes_capability_instance():
    engine = RuntimeEngine()
    capability = install_clock(engine)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )
    instance = engine.get_instance(session.session_id)

    stopped_session = engine.stop(session.session_id)

    assert instance.started is False
    assert stopped_session.state is RuntimeState.STOPPED

    with pytest.raises(CapabilityInstanceNotFoundError):
        engine.get_instance(session.session_id)


def test_get_unknown_instance_is_rejected():
    engine = RuntimeEngine()

    with pytest.raises(CapabilityInstanceNotFoundError):
        engine.get_instance("unknown-session")


def test_engine_accepts_factory_dependency():
    factory = CapabilityFactory()
    engine = RuntimeEngine(factory=factory)

    assert engine.factory is factory

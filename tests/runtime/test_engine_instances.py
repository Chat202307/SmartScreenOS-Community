import pytest

from src.smartscreen_runtime.runtime.engine import (
    CapabilityInstanceNotFoundError,
    RuntimeEngine,
)


def test_list_instances_is_empty_initially():
    engine = RuntimeEngine()

    assert engine.list_instances() == ()


def test_list_instances_contains_running_instance():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    instance = engine.get_instance(session.session_id)

    assert engine.list_instances() == (
        (session.session_id, instance),
    )

    engine.stop(session.session_id)


def test_list_instances_contains_multiple_instances():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    first = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )
    second = engine.start(
        capability.capability_id,
        session_id="session-clock-002",
    )

    first_instance = engine.get_instance(first.session_id)
    second_instance = engine.get_instance(second.session_id)

    assert engine.list_instances() == (
        (first.session_id, first_instance),
        (second.session_id, second_instance),
    )

    engine.stop(first.session_id)
    engine.stop(second.session_id)


def test_stopped_instance_is_removed_from_list():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    engine.stop(session.session_id)

    assert engine.list_instances() == ()


def test_get_instance_still_rejects_unknown_session():
    engine = RuntimeEngine()

    with pytest.raises(CapabilityInstanceNotFoundError):
        engine.get_instance("unknown-session")

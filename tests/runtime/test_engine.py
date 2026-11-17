import pytest

from src.smartscreen_runtime.runtime.capability_registry import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotRegisteredError,
)
from src.smartscreen_runtime.runtime.engine import RuntimeEngine


def test_install_capability():
    engine = RuntimeEngine()

    capability = engine.install("examples/capabilities/clock")

    assert capability.capability_id == "com.smartscreen.capability.clock"
    assert engine.registry.get(capability.capability_id) == capability
    assert engine.installed() == (capability,)


def test_duplicate_install_is_rejected():
    engine = RuntimeEngine()

    engine.install("examples/capabilities/clock")

    with pytest.raises(CapabilityAlreadyRegisteredError):
        engine.install("examples/capabilities/clock")


def test_uninstall_capability():
    engine = RuntimeEngine()

    capability = engine.install("examples/capabilities/clock")

    removed = engine.uninstall(capability.capability_id)

    assert removed == capability
    assert engine.installed() == ()
    assert len(engine.registry) == 0


def test_uninstall_unknown_capability_is_rejected():
    engine = RuntimeEngine()

    with pytest.raises(CapabilityNotRegisteredError):
        engine.uninstall("unknown-capability")


def test_engine_exposes_session_manager():
    engine = RuntimeEngine()

    assert len(engine.sessions) == 0

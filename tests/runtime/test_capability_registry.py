import pytest

from src.smartscreen_runtime.runtime.capability_loader import CapabilityLoader
from src.smartscreen_runtime.runtime.capability_registry import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotRegisteredError,
    CapabilityRegistry,
)


def load_clock_capability():
    return CapabilityLoader().load(
        "examples/capabilities/clock"
    )


def test_register_and_get_capability():
    registry = CapabilityRegistry()
    capability = load_clock_capability()

    registered = registry.register(capability)

    assert registered == capability
    assert registry.get(capability.capability_id) == capability
    assert len(registry) == 1


def test_duplicate_capability_is_rejected():
    registry = CapabilityRegistry()
    capability = load_clock_capability()

    registry.register(capability)

    with pytest.raises(CapabilityAlreadyRegisteredError):
        registry.register(capability)


def test_list_capabilities():
    registry = CapabilityRegistry()
    capability = load_clock_capability()

    registry.register(capability)

    assert registry.list() == (capability,)


def test_unregister_capability():
    registry = CapabilityRegistry()
    capability = load_clock_capability()

    registry.register(capability)

    removed = registry.unregister(capability.capability_id)

    assert removed == capability
    assert len(registry) == 0

    with pytest.raises(CapabilityNotRegisteredError):
        registry.get(capability.capability_id)


def test_get_unknown_capability_is_rejected():
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotRegisteredError):
        registry.get("unknown-capability")


def test_unregister_unknown_capability_is_rejected():
    registry = CapabilityRegistry()

    with pytest.raises(CapabilityNotRegisteredError):
        registry.unregister("unknown-capability")


def test_contains_capability_id():
    registry = CapabilityRegistry()
    capability = load_clock_capability()

    assert capability.capability_id not in registry

    registry.register(capability)

    assert capability.capability_id in registry

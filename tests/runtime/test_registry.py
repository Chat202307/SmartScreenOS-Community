import pytest

from src.smartscreen_runtime.manifest.loader import ManifestLoader
from src.smartscreen_runtime.registry.errors import (
    CapabilityAlreadyRegisteredError,
    CapabilityNotFoundError,
)
from src.smartscreen_runtime.registry.registry import CapabilityRegistry


def load_clock_manifest():
    return ManifestLoader().load(
        "examples/capabilities/clock/manifest.yaml"
    )


def test_register_and_get_manifest():
    registry = CapabilityRegistry()
    manifest = load_clock_manifest()

    registry.register(manifest)

    assert registry.get(manifest.capability_id) == manifest
    assert len(registry) == 1


def test_duplicate_registration_is_rejected():
    registry = CapabilityRegistry()
    manifest = load_clock_manifest()

    registry.register(manifest)

    with pytest.raises(CapabilityAlreadyRegisteredError):
        registry.register(manifest)


def test_unregister_manifest():
    registry = CapabilityRegistry()
    manifest = load_clock_manifest()

    registry.register(manifest)
    removed = registry.unregister(manifest.capability_id)

    assert removed == manifest
    assert len(registry) == 0

    with pytest.raises(CapabilityNotFoundError):
        registry.get(manifest.capability_id)

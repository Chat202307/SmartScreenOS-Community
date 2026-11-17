from src.smartscreen_runtime.manifest.loader import ManifestLoader
from src.smartscreen_runtime.registry.registry import CapabilityRegistry
from src.smartscreen_runtime.runtime.core import RuntimeCore
from src.smartscreen_runtime.runtime.state import RuntimeState


def load_manifest():
    return ManifestLoader().load(
        "examples/capabilities/clock/manifest.yaml"
    )


def test_runtime_lifecycle():

    registry = CapabilityRegistry()

    runtime = RuntimeCore(registry)

    manifest = load_manifest()

    runtime.install(manifest)

    assert runtime.state(
        manifest.capability_id
    ) == RuntimeState.INSTALLED

    runtime.activate(
        manifest.capability_id
    )

    assert runtime.state(
        manifest.capability_id
    ) == RuntimeState.ACTIVE

    runtime.deactivate(
        manifest.capability_id
    )

    assert runtime.state(
        manifest.capability_id
    ) == RuntimeState.INACTIVE

    runtime.uninstall(
        manifest.capability_id
    )

    assert runtime.state(
        manifest.capability_id
    ) == RuntimeState.UNINSTALLED

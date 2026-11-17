from src.smartscreen_runtime.manifest.loader import ManifestLoader
from src.smartscreen_runtime.runtime.session import CapabilitySession
from src.smartscreen_runtime.runtime.state import RuntimeState


def load_manifest():
    return ManifestLoader().load(
        "examples/capabilities/clock/manifest.yaml"
    )


def test_create_capability_session():
    manifest = load_manifest()

    session = CapabilitySession(
        session_id="session-clock-001",
        manifest=manifest,
        state=RuntimeState.INSTALLED,
    )

    assert session.session_id == "session-clock-001"
    assert session.capability_id == manifest.capability_id
    assert session.manifest == manifest
    assert session.state == RuntimeState.INSTALLED


def test_update_capability_session_state():
    manifest = load_manifest()

    session = CapabilitySession(
        session_id="session-clock-001",
        manifest=manifest,
        state=RuntimeState.INSTALLED,
    )

    session.state = RuntimeState.ACTIVE

    assert session.state == RuntimeState.ACTIVE

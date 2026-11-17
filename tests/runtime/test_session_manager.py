import pytest

from src.smartscreen_runtime.manifest.loader import ManifestLoader
from src.smartscreen_runtime.runtime.session_manager import (
    CapabilitySessionAlreadyExistsError,
    CapabilitySessionManager,
    CapabilitySessionNotFoundError,
)
from src.smartscreen_runtime.runtime.state import RuntimeState


def load_manifest():
    return ManifestLoader().load(
        "examples/capabilities/clock/manifest.yaml"
    )


def test_create_and_get_session():
    manager = CapabilitySessionManager()
    manifest = load_manifest()

    session = manager.create(
        session_id="session-clock-001",
        manifest=manifest,
        state=RuntimeState.INSTALLED,
    )

    assert manager.get(session.session_id) == session
    assert session.capability_id == manifest.capability_id
    assert len(manager) == 1


def test_duplicate_session_is_rejected():
    manager = CapabilitySessionManager()
    manifest = load_manifest()

    manager.create(
        session_id="session-clock-001",
        manifest=manifest,
        state=RuntimeState.INSTALLED,
    )

    with pytest.raises(CapabilitySessionAlreadyExistsError):
        manager.create(
            session_id="session-clock-001",
            manifest=manifest,
            state=RuntimeState.INSTALLED,
        )


def test_list_sessions():
    manager = CapabilitySessionManager()
    manifest = load_manifest()

    session = manager.create(
        session_id="session-clock-001",
        manifest=manifest,
        state=RuntimeState.INSTALLED,
    )

    assert manager.list() == (session,)


def test_remove_session():
    manager = CapabilitySessionManager()
    manifest = load_manifest()

    session = manager.create(
        session_id="session-clock-001",
        manifest=manifest,
        state=RuntimeState.INSTALLED,
    )

    removed = manager.remove(session.session_id)

    assert removed == session
    assert len(manager) == 0

    with pytest.raises(CapabilitySessionNotFoundError):
        manager.get(session.session_id)

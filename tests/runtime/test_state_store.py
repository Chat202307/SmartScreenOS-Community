from src.smartscreen_runtime.runtime.state import RuntimeState
from src.smartscreen_runtime.runtime.state_store import CapabilityStateStore


def test_state_store():

    store = CapabilityStateStore()

    capability_id = "com.smartscreen.clock"

    assert store.get(
        capability_id
    ) == RuntimeState.UNINSTALLED

    store.set(
        capability_id,
        RuntimeState.INSTALLED,
    )

    assert store.get(
        capability_id
    ) == RuntimeState.INSTALLED

    store.set(
        capability_id,
        RuntimeState.ACTIVE,
    )

    assert store.get(
        capability_id
    ) == RuntimeState.ACTIVE

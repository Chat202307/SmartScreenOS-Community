from src.smartscreen_runtime.runtime.state import RuntimeState


def test_runtime_states():

    assert RuntimeState.INSTALLED.value == "installed"

    assert RuntimeState.ACTIVE.value == "active"

    assert RuntimeState.INACTIVE.value == "inactive"

    assert RuntimeState.UNINSTALLED.value == "uninstalled"

import pytest

from src.smartscreen_runtime.runtime.capability_api import (
    Capability,
    CapabilityContext,
)


class DemoCapability(Capability):
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self, context: CapabilityContext) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_capability_start_and_stop():
    capability = DemoCapability()
    context = CapabilityContext(
        session_id="session-test-001",
        capability_id="com.smartscreen.capability.test",
        configuration={},
        logger=__import__("logging").getLogger("test.capability"),
    )

    capability.start(context)
    capability.stop()

    assert capability.started is True
    assert capability.stopped is True


def test_context_is_created():
    context = CapabilityContext(
        session_id="session-test-001",
        capability_id="com.smartscreen.capability.test",
        configuration={},
        logger=__import__("logging").getLogger("test.capability"),
    )

    assert context is not None


def test_capability_is_abstract():
    with pytest.raises(TypeError):
        Capability()

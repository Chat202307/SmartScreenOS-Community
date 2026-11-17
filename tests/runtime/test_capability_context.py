import logging

from src.smartscreen_runtime.runtime.capability_api import CapabilityContext
from src.smartscreen_runtime.runtime.engine import RuntimeEngine


def test_context_contains_runtime_identity():
    context = CapabilityContext(
        session_id="session-clock-001",
        capability_id="com.smartscreen.capability.clock",
        configuration={},
        logger=logging.getLogger("test.clock"),
    )

    assert context.session_id == "session-clock-001"
    assert context.capability_id == "com.smartscreen.capability.clock"


def test_context_contains_configuration():
    configuration = {
        "timezone": "Asia/Shanghai",
        "format": "24h",
    }

    context = CapabilityContext(
        session_id="session-clock-001",
        capability_id="com.smartscreen.capability.clock",
        configuration=configuration,
        logger=logging.getLogger("test.clock"),
    )

    assert context.configuration == configuration


def test_context_contains_logger():
    logger = logging.getLogger("test.clock")

    context = CapabilityContext(
        session_id="session-clock-001",
        capability_id="com.smartscreen.capability.clock",
        configuration={},
        logger=logger,
    )

    assert context.logger is logger


def test_engine_injects_context_into_capability():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    instance = engine.get_instance(session.session_id)
    context = instance.context

    assert context is not None
    assert context.session_id == session.session_id
    assert context.capability_id == capability.capability_id
    assert context.configuration == capability.manifest.configuration
    assert context.logger.name == (
        "smartscreen.capability.com.smartscreen.capability.clock."
        "session-clock-001"
    )

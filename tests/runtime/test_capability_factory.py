from pathlib import Path

import pytest

from src.smartscreen_runtime.runtime.capability import CapabilityRuntime
from src.smartscreen_runtime.runtime.capability_api import CapabilityContext
from src.smartscreen_runtime.runtime.capability_factory import (
    CapabilityClassNotFoundError,
    CapabilityFactory,
    CapabilityModuleNotFoundError,
)
from src.smartscreen_runtime.runtime.capability_loader import CapabilityLoader


def load_clock_capability():
    return CapabilityLoader().load(
        "examples/capabilities/clock"
    )


def test_create_capability_instance():
    factory = CapabilityFactory()
    capability = load_clock_capability()

    instance = factory.create(capability)

    assert instance.__class__.__name__ == "ClockCapability"
    assert instance.started is False


def test_created_instance_can_start_and_stop():
    factory = CapabilityFactory()
    capability = load_clock_capability()

    instance = factory.create(capability)

    instance.start(CapabilityContext(
        session_id="session-test-001",
        capability_id="com.smartscreen.capability.test",
        configuration={},
        logger=__import__("logging").getLogger("test.capability"),
    ))
    assert instance.started is True

    instance.stop()
    assert instance.started is False


def test_missing_capability_module_is_rejected(tmp_path: Path):
    capability = load_clock_capability()

    runtime = CapabilityRuntime(
        root_path=tmp_path,
        manifest_path=capability.manifest_path,
        manifest=capability.manifest,
    )

    with pytest.raises(CapabilityModuleNotFoundError):
        CapabilityFactory().create(runtime)


def test_missing_entry_point_class_is_rejected(tmp_path: Path):
    capability = load_clock_capability()

    (tmp_path / "capability.py").write_text(
        "class OtherCapability:\n"
        "    pass\n"
    )

    runtime = CapabilityRuntime(
        root_path=tmp_path,
        manifest_path=capability.manifest_path,
        manifest=capability.manifest,
    )

    with pytest.raises(CapabilityClassNotFoundError):
        CapabilityFactory().create(runtime)

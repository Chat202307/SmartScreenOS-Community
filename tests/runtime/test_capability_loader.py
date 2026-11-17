from pathlib import Path

import pytest

from src.smartscreen_runtime.runtime.capability_loader import (
    CapabilityDirectoryNotFoundError,
    CapabilityLoader,
    CapabilityManifestLoadError,
    CapabilityManifestNotFoundError,
)


def test_load_capability():
    loader = CapabilityLoader()

    capability = loader.load("examples/capabilities/clock")

    assert capability.capability_id == "com.smartscreen.capability.clock"
    assert capability.manifest.name == "Clock"
    assert capability.entry_point == "ClockCapability"
    assert capability.root_path == Path(
        "examples/capabilities/clock"
    ).resolve()
    assert capability.manifest_path == (
        capability.root_path / "manifest.yaml"
    )


def test_root_path_is_absolute():
    capability = CapabilityLoader().load(
        "examples/capabilities/clock"
    )

    assert capability.root_path.is_absolute()
    assert capability.manifest_path.is_absolute()


def test_missing_capability_directory_is_rejected(tmp_path):
    missing_path = tmp_path / "missing-capability"

    with pytest.raises(CapabilityDirectoryNotFoundError):
        CapabilityLoader().load(missing_path)


def test_missing_manifest_is_rejected(tmp_path):
    capability_path = tmp_path / "capability"
    capability_path.mkdir()

    with pytest.raises(CapabilityManifestNotFoundError):
        CapabilityLoader().load(capability_path)


def test_invalid_manifest_is_rejected(tmp_path):
    capability_path = tmp_path / "invalid-capability"
    capability_path.mkdir()

    manifest_path = capability_path / "manifest.yaml"
    manifest_path.write_text(
        "manifestVersion: [invalid",
        encoding="utf-8",
    )

    with pytest.raises(CapabilityManifestLoadError):
        CapabilityLoader().load(capability_path)


def write_manifest(
    capability_path: Path,
    *,
    entry_point: str | None,
) -> None:
    lines = [
        'manifestVersion: "1.0"',
        "id: com.smartscreen.capability.test",
        "name: Test Capability",
        "category: Test",
        "version: 1.0.0",
        "provider: SmartScreenOS",
    ]

    if entry_point is not None:
        lines.append(f"entryPoint: {entry_point}")

    (capability_path / "manifest.yaml").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def test_missing_entry_point_is_rejected(tmp_path):
    from src.smartscreen_runtime.runtime.capability_loader import (
        CapabilityEntryPointMissingError,
    )

    capability_path = tmp_path / "missing-entry-point"
    capability_path.mkdir()
    write_manifest(
        capability_path,
        entry_point=None,
    )

    with pytest.raises(CapabilityEntryPointMissingError):
        CapabilityLoader().load(capability_path)


@pytest.mark.parametrize(
    "entry_point",
    [
        "clock.ClockCapability",
        "clock.py:ClockCapability",
        "Clock-Capability",
        "123ClockCapability",
        "Clock Capability",
    ],
)
def test_invalid_entry_point_is_rejected(
    tmp_path,
    entry_point,
):
    from src.smartscreen_runtime.runtime.capability_loader import (
        CapabilityEntryPointInvalidError,
    )

    capability_path = tmp_path / "invalid-entry-point"
    capability_path.mkdir()
    write_manifest(
        capability_path,
        entry_point=entry_point,
    )

    with pytest.raises(CapabilityEntryPointInvalidError):
        CapabilityLoader().load(capability_path)


def test_valid_entry_point_is_accepted(tmp_path):
    capability_path = tmp_path / "valid-entry-point"
    capability_path.mkdir()
    write_manifest(
        capability_path,
        entry_point="TestCapability",
    )

    capability = CapabilityLoader().load(capability_path)

    assert capability.entry_point == "TestCapability"

from src.smartscreen_runtime.manifest.loader import ManifestLoader


def test_load_manifest():
    loader = ManifestLoader()

    manifest = loader.load(
        "examples/capabilities/clock/manifest.yaml"
    )

    assert manifest.capability_id == "com.smartscreen.capability.clock"
    assert manifest.name == "Clock"
    assert manifest.category == "System"
    assert manifest.provider == "SmartScreenOS"
    assert manifest.manifest_version == "1.0"

from src.smartscreen_runtime.manifest.loader import ManifestLoader
from src.smartscreen_runtime.manifest.validator import (
    ManifestValidator,
)


def test_validate_manifest():
    loader = ManifestLoader()

    manifest = loader.load(
        "examples/capabilities/clock/manifest.yaml"
    )

    validator = ManifestValidator()

    validator.validate(manifest)
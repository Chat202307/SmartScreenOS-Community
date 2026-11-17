from __future__ import annotations

from .model import CapabilityManifest


class ManifestValidationError(ValueError):
    """Raised when a capability manifest is invalid."""


class ManifestValidator:
    def validate(self, manifest: CapabilityManifest) -> None:
        if not manifest.manifest_version:
            raise ManifestValidationError(
                "manifestVersion is required."
            )

        if manifest.manifest_version != "1.0":
            raise ManifestValidationError(
                "Unsupported manifestVersion."
            )

        if not manifest.capability_id:
            raise ManifestValidationError(
                "id is required."
            )

        if not manifest.name:
            raise ManifestValidationError(
                "name is required."
            )

        if not manifest.category:
            raise ManifestValidationError(
                "category is required."
            )

        if not manifest.version:
            raise ManifestValidationError(
                "version is required."
            )

        if not manifest.provider:
            raise ManifestValidationError(
                "provider is required."
            )

from __future__ import annotations

from pathlib import Path

from ..manifest.loader import ManifestLoader
from ..manifest.model import CapabilityManifest
from .capability import CapabilityRuntime


class CapabilityLoaderError(Exception):
    """Base exception for capability loading errors."""


class CapabilityDirectoryNotFoundError(CapabilityLoaderError):
    """Raised when the capability root directory does not exist."""


class CapabilityManifestNotFoundError(CapabilityLoaderError):
    """Raised when manifest.yaml is missing from a capability directory."""


class CapabilityManifestLoadError(CapabilityLoaderError):
    """Raised when a capability manifest cannot be parsed or constructed."""


class CapabilityEntryPointMissingError(CapabilityLoaderError):
    """Raised when a capability manifest has no entry point."""


class CapabilityEntryPointInvalidError(CapabilityLoaderError):
    """Raised when a capability entry point has an invalid format."""


class CapabilityLoader:
    """Load and validate a capability directory."""

    def __init__(self, manifest_loader: ManifestLoader | None = None) -> None:
        self._manifest_loader = manifest_loader or ManifestLoader()

    def load(self, capability_path: str | Path) -> CapabilityRuntime:
        root_path = Path(capability_path).expanduser().resolve()

        self._validate_root_path(root_path)

        manifest_path = root_path / "manifest.yaml"
        self._validate_manifest_path(manifest_path)

        manifest = self._load_manifest(manifest_path)
        self._validate_entry_point(manifest)

        return CapabilityRuntime(
            root_path=root_path,
            manifest_path=manifest_path,
            manifest=manifest,
        )

    @staticmethod
    def _validate_root_path(root_path: Path) -> None:
        if not root_path.is_dir():
            raise CapabilityDirectoryNotFoundError(
                f"Capability directory not found: {root_path}"
            )

    @staticmethod
    def _validate_manifest_path(manifest_path: Path) -> None:
        if not manifest_path.is_file():
            raise CapabilityManifestNotFoundError(
                f"Capability manifest not found: {manifest_path}"
            )

    def _load_manifest(
        self,
        manifest_path: Path,
    ) -> CapabilityManifest:
        try:
            return self._manifest_loader.load(manifest_path)
        except Exception as exc:
            raise CapabilityManifestLoadError(
                f"Unable to load capability manifest: {manifest_path}"
            ) from exc

    @staticmethod
    def _validate_entry_point(manifest: CapabilityManifest) -> None:
        entry_point = manifest.entry_point.strip()

        if not entry_point:
            raise CapabilityEntryPointMissingError(
                f"Capability entry point is missing: "
                f"{manifest.capability_id}"
            )

        if not entry_point.isidentifier():
            raise CapabilityEntryPointInvalidError(
                f"Invalid capability entry point "
                f"{entry_point!r}: {manifest.capability_id}"
            )

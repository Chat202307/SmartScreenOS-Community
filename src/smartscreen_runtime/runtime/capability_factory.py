from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from .capability import CapabilityRuntime


class CapabilityFactoryError(Exception):
    """Base exception for capability factory errors."""


class CapabilityModuleNotFoundError(CapabilityFactoryError):
    """Raised when capability.py cannot be found."""


class CapabilityModuleLoadError(CapabilityFactoryError):
    """Raised when capability.py cannot be imported."""


class CapabilityClassNotFoundError(CapabilityFactoryError):
    """Raised when the configured entry-point class cannot be found."""


class CapabilityInstantiationError(CapabilityFactoryError):
    """Raised when the entry-point class cannot be instantiated."""


class CapabilityFactory:
    """Load and instantiate a capability entry-point class."""

    MODULE_FILENAME = "capability.py"

    def create(self, capability: CapabilityRuntime) -> Any:
        module_path = capability.root_path / self.MODULE_FILENAME

        if not module_path.is_file():
            raise CapabilityModuleNotFoundError(
                f"Capability module not found: {module_path}"
            )

        module = self._load_module(
            module_path=module_path,
            capability_id=capability.capability_id,
        )

        entry_point = self._get_entry_point(
            module=module,
            entry_point=capability.entry_point,
            capability_id=capability.capability_id,
        )

        try:
            return entry_point()
        except Exception as exc:
            raise CapabilityInstantiationError(
                f"Unable to instantiate capability entry point "
                f"{capability.entry_point!r}: {capability.capability_id}"
            ) from exc

    @staticmethod
    def _load_module(
        module_path: Path,
        capability_id: str,
    ) -> ModuleType:
        module_name = (
            "_smartscreen_capability_"
            + capability_id.replace(".", "_").replace("-", "_")
        )

        spec = importlib.util.spec_from_file_location(
            module_name,
            module_path,
        )

        if spec is None or spec.loader is None:
            raise CapabilityModuleLoadError(
                f"Unable to create module spec: {module_path}"
            )

        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise CapabilityModuleLoadError(
                f"Unable to load capability module: {module_path}"
            ) from exc

        return module

    @staticmethod
    def _get_entry_point(
        module: ModuleType,
        entry_point: str,
        capability_id: str,
    ) -> type[Any]:
        candidate = getattr(module, entry_point, None)

        if not isinstance(candidate, type):
            raise CapabilityClassNotFoundError(
                f"Capability entry-point class "
                f"{entry_point!r} not found: {capability_id}"
            )

        return candidate

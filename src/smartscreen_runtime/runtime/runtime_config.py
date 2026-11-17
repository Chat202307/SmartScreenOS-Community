from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


class RuntimeConfigError(ValueError):
    """Raised when runtime configuration cannot be loaded or validated."""


@dataclass(frozen=True, slots=True)
class CapabilityConfig:
    path: str
    session_id: str
    configuration: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    scheduler_interval_seconds: float
    capabilities: tuple[CapabilityConfig, ...]


class RuntimeConfigLoader:
    """Load SmartScreenOS runtime configuration from YAML."""

    def load(self, path: str | Path) -> RuntimeConfig:
        config_path = Path(path)

        if not config_path.is_file():
            raise RuntimeConfigError(
                f"Runtime configuration not found: {config_path}"
            )

        try:
            raw = yaml.safe_load(
                config_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            raise RuntimeConfigError(
                f"Unable to parse runtime YAML: {config_path}"
            ) from exc

        if raw is None:
            raw = {}

        if not isinstance(raw, Mapping):
            raise RuntimeConfigError(
                "Runtime YAML root must be a mapping."
            )

        scheduler_interval_seconds = self._load_scheduler(raw)
        capabilities = self._load_capabilities(raw)

        return RuntimeConfig(
            scheduler_interval_seconds=scheduler_interval_seconds,
            capabilities=capabilities,
        )

    @staticmethod
    def _load_scheduler(
        raw: Mapping[str, Any],
    ) -> float:
        scheduler = raw.get("scheduler", {})

        if scheduler is None:
            scheduler = {}

        if not isinstance(scheduler, Mapping):
            raise RuntimeConfigError(
                "Runtime scheduler configuration must be a mapping."
            )

        interval = scheduler.get("intervalSeconds", 1.0)

        if (
            not isinstance(interval, (int, float))
            or isinstance(interval, bool)
            or interval <= 0
        ):
            raise RuntimeConfigError(
                "Runtime scheduler interval must be greater than zero."
            )

        return float(interval)

    @staticmethod
    def _load_capabilities(
        raw: Mapping[str, Any],
    ) -> tuple[CapabilityConfig, ...]:
        capabilities_raw = raw.get("capabilities", [])

        if capabilities_raw is None:
            capabilities_raw = []

        if not isinstance(capabilities_raw, list):
            raise RuntimeConfigError(
                "Runtime capabilities must be a list."
            )

        capabilities: list[CapabilityConfig] = []
        session_ids: set[str] = set()

        for index, item in enumerate(capabilities_raw):
            if not isinstance(item, Mapping):
                raise RuntimeConfigError(
                    f"Capability at index {index} must be a mapping."
                )

            path = item.get("path")
            if not isinstance(path, str) or not path.strip():
                raise RuntimeConfigError(
                    f"Capability at index {index} requires a non-empty path."
                )

            session_id = item.get("sessionId")
            if (
                not isinstance(session_id, str)
                or not session_id.strip()
            ):
                raise RuntimeConfigError(
                    f"Capability at index {index} "
                    "requires a non-empty sessionId."
                )

            if session_id in session_ids:
                raise RuntimeConfigError(
                    f"duplicate sessionId: {session_id}"
                )

            session_ids.add(session_id)

            configuration = item.get("configuration", {})

            if configuration is None:
                configuration = {}

            if not isinstance(configuration, Mapping):
                raise RuntimeConfigError(
                    f"Capability at index {index} "
                    "has invalid configuration."
                )

            capabilities.append(
                CapabilityConfig(
                    path=path.strip(),
                    session_id=session_id.strip(),
                    configuration=dict(configuration),
                )
            )

        return tuple(capabilities)

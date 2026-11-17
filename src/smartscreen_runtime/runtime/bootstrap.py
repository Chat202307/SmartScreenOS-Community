from __future__ import annotations

import time
from pathlib import Path
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .engine import RuntimeEngine
from .host import RuntimeHost
from .runtime_config import RuntimeConfigLoader
from .scheduler import RuntimeScheduler
from .session_manager import CapabilitySessionNotFoundError


class RuntimeBootstrapError(RuntimeError):
    """Raised when runtime bootstrap cannot be completed."""


def _validate_capabilities(
    capabilities: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    configs = list(capabilities)
    session_ids: set[str] = set()

    for index, config in enumerate(configs):
        if not isinstance(config, Mapping):
            raise RuntimeBootstrapError(
                f"Capability configuration at index {index} "
                "must be a mapping."
            )

        path = config.get("path")
        if not isinstance(path, str) or not path.strip():
            raise RuntimeBootstrapError(
                f"Capability configuration at index {index} "
                "requires a non-empty path."
            )

        session_id = config.get("session_id")
        if (
            not isinstance(session_id, str)
            or not session_id.strip()
        ):
            raise RuntimeBootstrapError(
                f"Capability configuration at index {index} "
                "requires a non-empty session_id."
            )

        if session_id in session_ids:
            raise RuntimeBootstrapError(
                f"duplicate session_id: {session_id}"
            )

        session_ids.add(session_id)

        configuration = config.get("configuration")
        if (
            configuration is not None
            and not isinstance(configuration, Mapping)
        ):
            raise RuntimeBootstrapError(
                f"Capability configuration at index {index} "
                "has invalid configuration."
            )

    return configs


def _rollback_bootstrap(
    engine: RuntimeEngine,
    session_ids: list[str],
    capability_ids: list[str],
) -> None:
    # Stop any instances that were successfully started.
    for session_id in reversed(session_ids):
        try:
            engine.get_instance(session_id)
        except Exception:
            pass
        else:
            try:
                engine.stop(session_id)
            except Exception:
                pass

    # Remove sessions created during this bootstrap attempt,
    # including FAILED and STOPPED sessions.
    for session_id in reversed(session_ids):
        try:
            engine.sessions.remove(session_id)
        except CapabilitySessionNotFoundError:
            pass

    # Uninstall only capabilities installed by this bootstrap attempt.
    for capability_id in reversed(capability_ids):
        try:
            engine.uninstall(capability_id)
        except Exception:
            pass


def create_runtime_host(
    *,
    scheduler_interval_seconds: float = 1.0,
    clock: Callable[[], float] | None = None,
    capabilities: Iterable[Mapping[str, Any]] | None = None,
    engine: RuntimeEngine | None = None,
) -> RuntimeHost:
    """Create and optionally bootstrap the SmartScreenOS runtime host."""

    resolved_clock = clock or time.monotonic

    capability_configs = (
        _validate_capabilities(capabilities)
        if capabilities is not None
        else []
    )

    resolved_engine = engine or RuntimeEngine()

    scheduler = RuntimeScheduler(
        resolved_engine,
        interval_seconds=scheduler_interval_seconds,
        start_time=resolved_clock(),
        clock=resolved_clock,
    )

    host = RuntimeHost(
        engine=resolved_engine,
        scheduler=scheduler,
    )

    bootstrap_session_ids: list[str] = []
    installed_capability_ids: list[str] = []

    try:
        for config in capability_configs:
            session_id = config["session_id"]

            # Record before start(), because start() may create a FAILED
            # session before raising.
            bootstrap_session_ids.append(session_id)

            capability = resolved_engine.install(config["path"])
            installed_capability_ids.append(
                capability.capability_id
            )

            resolved_engine.start(
                capability.capability_id,
                session_id=session_id,
                configuration=(
                    dict(config["configuration"])
                    if config.get("configuration") is not None
                    else None
                ),
            )

    except Exception as exc:
        _rollback_bootstrap(
            resolved_engine,
            bootstrap_session_ids,
            installed_capability_ids,
        )

        raise RuntimeBootstrapError(
            "Unable to bootstrap runtime capabilities."
        ) from exc

    return host


def create_runtime_host_from_config(
    config_path: str | Path,
    *,
    clock: Callable[[], float] | None = None,
    engine: RuntimeEngine | None = None,
) -> RuntimeHost:
    """Create a runtime host from a YAML configuration file."""

    config = RuntimeConfigLoader().load(config_path)

    capabilities = [
        {
            "path": capability.path,
            "session_id": capability.session_id,
            "configuration": dict(capability.configuration),
        }
        for capability in config.capabilities
    ]

    return create_runtime_host(
        scheduler_interval_seconds=(
            config.scheduler_interval_seconds
        ),
        clock=clock,
        capabilities=capabilities,
        engine=engine,
    )

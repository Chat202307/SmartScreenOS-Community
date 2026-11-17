from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class CapabilityContext:
    """Runtime identity, configuration, and services for a capability."""

    session_id: str
    capability_id: str
    configuration: Mapping[str, Any]
    logger: logging.Logger


class Capability(ABC):
    """Base interface implemented by all executable capabilities."""

    @abstractmethod
    def start(self, context: CapabilityContext) -> None:
        """Start the capability using the supplied runtime context."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the capability and release its runtime resources."""

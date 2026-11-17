"""Adapter contract for SmartScreen OS."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

StateCallback = Callable[[str, bool, str, Dict[str, Any]], None]


class AdapterError(RuntimeError):
    pass


class BaseAdapter(ABC):
    adapter_id = "base"

    def __init__(self, state_callback: StateCallback) -> None:
        self._state_callback = state_callback

    @abstractmethod
    def start(self) -> None:
        """Start adapter resources."""

    @abstractmethod
    def stop(self) -> None:
        """Stop adapter resources."""

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Return adapter health."""

    @abstractmethod
    def send_command(
        self,
        device_id: str,
        command: str,
        value: Any = None,
    ) -> None:
        """Send a normalized command."""

    def publish_state(
        self,
        device_id: str,
        *,
        available: bool,
        state: str,
        attributes: Dict[str, Any] | None = None,
    ) -> None:
        self._state_callback(
            device_id,
            available,
            state,
            attributes or {},
        )

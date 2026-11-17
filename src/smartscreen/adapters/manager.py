"""Adapter manager."""

from __future__ import annotations

from typing import Any, Dict

from .base import AdapterError, BaseAdapter


class AdapterManager:
    def __init__(self) -> None:
        self._adapters: Dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter) -> None:
        adapter_id = adapter.adapter_id
        if adapter_id in self._adapters:
            raise AdapterError(f"Duplicate adapter id: {adapter_id}")
        self._adapters[adapter_id] = adapter

    def start_all(self) -> None:
        for adapter in self._adapters.values():
            adapter.start()

    def stop_all(self) -> None:
        for adapter in reversed(list(self._adapters.values())):
            adapter.stop()

    def health(self) -> Dict[str, Dict[str, Any]]:
        return {
            adapter_id: adapter.health()
            for adapter_id, adapter in self._adapters.items()
        }

    def send_command(
        self,
        adapter_id: str,
        device_id: str,
        command: str,
        value: Any = None,
    ) -> None:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            raise AdapterError(f"Adapter not found: {adapter_id}")

        adapter.send_command(device_id, command, value)

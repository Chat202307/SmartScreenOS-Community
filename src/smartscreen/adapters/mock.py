"""Mock adapter used before real backends are connected."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .base import AdapterError, BaseAdapter


class MockAdapter(BaseAdapter):
    adapter_id = "mock"

    def __init__(self, state_callback, state_file: Path) -> None:
        super().__init__(state_callback)
        self._state_file = state_file
        self._running = False
        self._states: Dict[str, Dict[str, Any]] = {}

    def start(self) -> None:
        if not self._state_file.exists():
            raise AdapterError(f"Mock state file not found: {self._state_file}")

        data = json.loads(self._state_file.read_text(encoding="utf-8"))
        self._states = dict(data.get("states", {}))
        self._running = True

        for device_id, payload in self._states.items():
            self.publish_state(
                device_id,
                available=bool(payload.get("available", True)),
                state=str(payload.get("state", "unknown")),
                attributes=dict(payload.get("attributes", {})),
            )

    def stop(self) -> None:
        self._running = False

    def health(self):
        return {
            "adapter_id": self.adapter_id,
            "running": self._running,
            "device_count": len(self._states),
        }

    def send_command(self, device_id: str, command: str, value: Any = None) -> None:
        if not self._running:
            raise AdapterError("Mock adapter is not running.")

        payload = self._states.setdefault(
            device_id,
            {
                "available": True,
                "state": "unknown",
                "attributes": {},
            },
        )

        if command == "turn_on":
            payload["state"] = "on"
        elif command == "turn_off":
            payload["state"] = "off"
        elif command == "open":
            payload["state"] = "opening"
        elif command == "close":
            payload["state"] = "closing"
        elif command == "stop":
            payload["state"] = "stopped"
        elif command == "set_mode":
            payload["state"] = str(value)
            payload.setdefault("attributes", {})["power"] = (
                "off" if value == "off" else "on"
            )
        elif command == "set_temperature":
            payload.setdefault("attributes", {})["target_temperature"] = value
        elif command == "set_fan_mode":
            payload.setdefault("attributes", {})["fan_mode"] = value
        else:
            raise AdapterError(f"Unsupported mock command: {command}")

        self.publish_state(
            device_id,
            available=bool(payload.get("available", True)),
            state=str(payload.get("state", "unknown")),
            attributes=dict(payload.get("attributes", {})),
        )

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock


class HouseModel:
    def __init__(self, home_config, rooms, devices, states, event_bus):
        self._lock = RLock()
        self._home_config = home_config
        self._rooms = rooms
        self._devices = devices
        self._states = states
        self._event_bus = event_bus
        self._activity = []
        self._activity_limit = 100

        self._event_bus.subscribe(
            "device.state_changed",
            self._on_device_state_changed,
        )

    def _on_device_state_changed(self, event):
        payload = dict(event.payload)
        device_id = payload.get("device_id")
        device = self._devices.get(device_id)

        if device is None:
            return

        with self._lock:
            self._activity.append({
                "time": event.created_at,
                "room_id": device.room,
                "device_id": device.id,
                "device_name": device.name,
                "state": payload.get("state", "unknown"),
                "available": bool(payload.get("available", False)),
                "previous": deepcopy(payload.get("previous")),
                "current": deepcopy(payload.get("current")),
            })
            self._activity = self._activity[-self._activity_limit:]

    def snapshot(self):
        with self._lock:
            state_snapshot = self._states.snapshot()
            rooms_payload = []
            total_devices = 0
            total_available = 0

            for room in self._rooms.all():
                room_devices = self._devices.by_room(room.id)
                total_devices += len(room_devices)

                available = 0
                unavailable = 0
                active = 0
                last_activity = None
                devices_payload = []

                for device in room_devices:
                    state = state_snapshot[device.id]

                    if state.available:
                        available += 1
                        total_available += 1
                    else:
                        unavailable += 1

                    if self._is_active(device.type, state.state):
                        active += 1

                    devices_payload.append({
                        "id": device.id,
                        "name": device.name,
                        "type": device.type,
                        "available": state.available,
                        "state": state.state,
                        "attributes": deepcopy(state.attributes),
                        "updated_at": state.updated_at,
                    })

                for item in reversed(self._activity):
                    if item["room_id"] == room.id:
                        last_activity = dict(item)
                        break

                rooms_payload.append({
                    "id": room.id,
                    "name": room.name,
                    "area": room.area,
                    "order": room.order,
                    "status": self._room_status(
                        total=len(room_devices),
                        available=available,
                        unavailable=unavailable,
                        active=active,
                    ),
                    "device_count": len(room_devices),
                    "available_devices": available,
                    "unavailable_devices": unavailable,
                    "active_devices": active,
                    "last_activity": last_activity,
                    "devices": devices_payload,
                })

            now = datetime.now(timezone.utc).isoformat()
            home = self._home_config["home"]

            return {
                "generated_at": now,
                "home": {
                    "name": home["name"],
                    "room_count": len(rooms_payload),
                    "device_count": total_devices,
                    "available_devices": total_available,
                    "unavailable_devices": total_devices - total_available,
                    "status": (
                        "healthy"
                        if total_devices == total_available
                        else "degraded"
                    ),
                },
                "rooms": rooms_payload,
                "recent_activity": list(
                    reversed(deepcopy(self._activity[-20:]))
                ),
            }

    @staticmethod
    def _is_active(device_type, state):
        if device_type == "light":
            return state == "on"
        if device_type == "climate":
            return state not in ("off", "unknown")
        if device_type == "curtain":
            return state in ("open", "opening", "closing", "stopped")
        if device_type == "occupancy":
            return state == "on"
        return False

    @staticmethod
    def _room_status(total, available, unavailable, active):
        if total == 0:
            return "empty"
        if available == 0:
            return "offline"
        if unavailable > 0:
            return "partial"
        if active > 0:
            return "active"
        return "idle"

from copy import deepcopy
from threading import RLock


class FeedGenerator:
    def __init__(self, devices, event_bus, history_limit=100):
        self._lock = RLock()
        self._devices = devices
        self._event_bus = event_bus
        self._history_limit = int(history_limit)
        self._items = []

        self._event_bus.subscribe(
            "device.state_changed",
            self._on_device_state_changed,
        )
        self._event_bus.subscribe(
            "adapter.connected",
            self._on_adapter_connected,
        )
        self._event_bus.subscribe(
            "adapter.reconnecting",
            self._on_adapter_reconnecting,
        )

    def _append(self, item):
        with self._lock:
            self._items.append(deepcopy(item))
            self._items = self._items[-self._history_limit:]

    def _on_device_state_changed(self, event):
        payload = dict(event.payload)
        previous = payload.get("previous")
        current = payload.get("current") or {}
        device_id = payload.get("device_id")
        device = self._devices.get(device_id)

        if device is None:
            return

        # Initial retained-state synchronization is not family activity.
        if previous is None:
            return

        text = self._device_text(
            device,
            previous,
            current,
        )

        if text is None:
            return

        self._append({
            "time": event.created_at,
            "kind": "home",
            "icon": self._icon(device.type),
            "title": device.name,
            "text": text,
            "room_id": device.room,
            "device_id": device.id,
            "source_event": event.name,
        })

    def _on_adapter_connected(self, event):
        adapter = str(event.payload.get("adapter", "adapter")).upper()
        self._append({
            "time": event.created_at,
            "kind": "system",
            "icon": "●",
            "title": adapter,
            "text": "连接已恢复",
            "room_id": None,
            "device_id": None,
            "source_event": event.name,
        })

    def _on_adapter_reconnecting(self, event):
        adapter = str(event.payload.get("adapter", "adapter")).upper()
        self._append({
            "time": event.created_at,
            "kind": "system",
            "icon": "○",
            "title": adapter,
            "text": "正在重新连接",
            "room_id": None,
            "device_id": None,
            "source_event": event.name,
        })

    def snapshot(self, limit=20, include_system=False):
        with self._lock:
            items = list(reversed(deepcopy(self._items)))

        if not include_system:
            items = [
                item for item in items
                if item["kind"] != "system"
            ]

        return items[:int(limit)]

    @staticmethod
    def _icon(device_type):
        return {
            "light": "💡",
            "curtain": "🪟",
            "climate": "❄",
            "occupancy": "🚶",
        }.get(device_type, "⌂")

    @staticmethod
    def _device_text(device, previous, current):
        old_state = str(previous.get("state", "unknown"))
        new_state = str(current.get("state", "unknown"))

        if device.type == "light":
            if old_state != new_state:
                if new_state == "on":
                    return "已开启"
                if new_state == "off":
                    return "已关闭"

        if device.type == "curtain":
            if old_state != new_state:
                mapping = {
                    "open": "已打开",
                    "closed": "已关闭",
                    "opening": "正在打开",
                    "closing": "正在关闭",
                    "stopped": "已停止",
                }
                return mapping.get(new_state)

        if device.type == "climate":
            if old_state != new_state:
                mapping = {
                    "cool": "开始制冷",
                    "heat": "开始制热",
                    "off": "已关闭",
                }
                return mapping.get(new_state)

            old_attributes = previous.get("attributes") or {}
            new_attributes = current.get("attributes") or {}

            old_target = old_attributes.get("target_temperature")
            new_target = new_attributes.get("target_temperature")

            if old_target != new_target and new_target is not None:
                return "设定温度调整为 %s℃" % new_target

        if device.type == "occupancy":
            if old_state != new_state:
                if new_state == "on":
                    return "检测到有人活动"
                if new_state == "off":
                    return "恢复无人状态"

        if bool(previous.get("available")) != bool(current.get("available")):
            if current.get("available"):
                return "已恢复在线"
            return "暂时无法连接"

        return None

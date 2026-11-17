from datetime import datetime, timezone
from threading import RLock

class ConnectionManager:
    def __init__(self, history_limit=100):
        self._lock = RLock()
        self._history_limit = history_limit
        self._connections = {}
        self._events = []

    def register(self, connection_id):
        with self._lock:
            if connection_id not in self._connections:
                self._connections[connection_id] = {
                    "state": "disconnected",
                    "connected": False,
                    "last_change": None,
                    "last_connected": None,
                    "last_disconnected": None,
                    "reconnect_count": 0,
                    "message_count": 0,
                    "last_message": None,
                }

    def set_state(self, connection_id, state, detail=""):
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self.register(connection_id)
            item = self._connections[connection_id]
            previous = item["state"]
            if previous == state:
                return

            item["state"] = state
            item["connected"] = state == "connected"
            item["last_change"] = now

            if state == "connected":
                if previous in ("disconnected", "reconnecting"):
                    item["reconnect_count"] += 1
                item["last_connected"] = now
            elif state == "disconnected":
                item["last_disconnected"] = now

            self._events.append({
                "time": now,
                "connection": connection_id,
                "from": previous,
                "to": state,
                "detail": detail,
            })
            self._events = self._events[-self._history_limit:]

    def mark_message(self, connection_id):
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self.register(connection_id)
            item = self._connections[connection_id]
            item["message_count"] += 1
            item["last_message"] = now

    def snapshot(self):
        with self._lock:
            return {
                "connections": {
                    key: dict(value)
                    for key, value in self._connections.items()
                },
                "events": list(reversed(self._events[-20:])),
            }

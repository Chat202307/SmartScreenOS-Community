from datetime import datetime, timezone

class DiagnosticsEngine:
    def __init__(self, core, devices, states):
        self.core = core
        self.devices = devices
        self.states = states
        self.started_at = datetime.now(timezone.utc)

    def _connection_snapshot(self):
        manager = getattr(self.core, "connections", None)
        if manager is None:
            return {
                "connections": {},
                "events": [],
            }

        snapshot = manager.snapshot()
        return {
            "connections": dict(snapshot.get("connections", {})),
            "events": list(snapshot.get("events", [])),
        }

    def snapshot(self):
        adapters = self.core.adapters.health()
        states = self.states.snapshot()
        total = len(self.devices.all())
        available = sum(1 for item in states.values() if item.available)

        latest = None
        for item in states.values():
            if item.updated_at and (latest is None or item.updated_at > latest):
                latest = item.updated_at

        connection_snapshot = self._connection_snapshot()
        connections = connection_snapshot["connections"]
        events = connection_snapshot["events"]

        overall = "healthy"

        if connections:
            for item in connections.values():
                if item.get("state") != "connected":
                    overall = "degraded"
                    break
        else:
            for item in adapters.values():
                connected = item.get(
                    "connected",
                    item.get("running", False),
                )
                if not connected:
                    overall = "degraded"
                    break

        return {
            "overall": overall,
            "time": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(
                (
                    datetime.now(timezone.utc)
                    - self.started_at
                ).total_seconds()
            ),
            "devices": {
                "total": total,
                "available": available,
                "unavailable": total - available,
                "last_update": latest,
            },
            "adapters": adapters,
            "connections": connections,
            "events": events,
            "cache_policy": {
                "hold_last_state_seconds": 120,
                "warning_after_seconds": 30,
            },
        }

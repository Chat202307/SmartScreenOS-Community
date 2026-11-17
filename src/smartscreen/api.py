"""SmartScreen OS REST API and dashboard server."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .dashboard import DashboardEngine
from .diagnostics import DiagnosticsEngine


def success(data):
    return {"ok": True, "data": data}


def error(code, message):
    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


class ApiApplication:
    def __init__(self, config, rooms, devices, states, core=None) -> None:
        self.config = config
        self.rooms = rooms
        self.devices = devices
        self.states = states
        self.core = core
        self.dashboard = DashboardEngine(
            config,
            rooms,
            devices,
            states,
        )
        self.diagnostics = (
            DiagnosticsEngine(core, devices, states)
            if core is not None else None
        )

    def system_payload(self):
        system = self.config["system"]["system"]
        home = self.config["home"]["home"]

        adapters = {}
        if self.core is not None:
            adapters = self.core.adapters.health()

        return {
            "name": system["name"],
            "version": system["version"],
            "home_name": home["name"],
            "time": datetime.now(timezone.utc).isoformat(),
            "status": "online",
            "development_port": system["development_port"],
            "stable_port": system["stable_port"],
            "adapters": adapters,
        }

    def health_payload(self):
        if self.diagnostics is None:
            return {
                "overall": "unknown",
                "time": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": 0,
                "devices": {
                    "total": len(self.devices.all()),
                    "available": 0,
                    "unavailable": len(self.devices.all()),
                    "last_update": None,
                },
                "adapters": {},
            }
        return self.diagnostics.snapshot()

    def events_payload(self):
        if self.core is None:
            return {
                "stats": {
                    "published_count": 0,
                    "history_count": 0,
                    "subscriber_groups": 0,
                    "subscriber_count": 0,
                },
                "events": [],
            }

        return {
            "stats": self.core.events.stats(),
            "events": [
                {
                    "name": item.name,
                    "source": item.source,
                    "payload": item.payload,
                    "created_at": item.created_at,
                }
                for item in self.core.events.recent(50)
            ],
        }

    def house_payload(self):
        if self.core is None:
            return {
                "generated_at": None,
                "home": {
                    "name": self.config["home"]["home"]["name"],
                    "room_count": len(self.rooms.all()),
                    "device_count": len(self.devices.all()),
                    "available_devices": 0,
                    "unavailable_devices": len(self.devices.all()),
                    "status": "unknown",
                },
                "rooms": [],
                "recent_activity": [],
            }

        return self.core.house.snapshot()

    def house_home_payload(self):
        if self.core is None:
            return self.dashboard.home()

        house = self.core.house.snapshot()
        legacy = self.dashboard.home()

        rooms = []
        for room in house["rooms"]:
            type_counts = {
                "light": 0,
                "curtain": 0,
                "climate": 0,
                "occupancy": 0,
            }
            active_counts = {
                "light": 0,
                "curtain": 0,
                "climate": 0,
                "occupancy": 0,
            }

            for device in room["devices"]:
                device_type = device["type"]
                if device_type in type_counts:
                    type_counts[device_type] += 1

                if device_type == "light" and device["state"] == "on":
                    active_counts["light"] += 1
                elif device_type == "curtain" and device["state"] in (
                    "open",
                    "opening",
                    "closing",
                    "stopped",
                ):
                    active_counts["curtain"] += 1
                elif device_type == "climate" and device["state"] not in (
                    "off",
                    "unknown",
                ):
                    active_counts["climate"] += 1
                elif device_type == "occupancy" and device["state"] == "on":
                    active_counts["occupancy"] += 1

            rooms.append({
                "id": room["id"],
                "name": room["name"],
                "area": room["area"],
                "order": room["order"],
                "status": room["status"],
                "device_count": room["device_count"],
                "available_devices": room["available_devices"],
                "unavailable_devices": room["unavailable_devices"],
                "active_devices": room["active_devices"],
                "last_activity": room["last_activity"],
                "type_counts": type_counts,
                "active_counts": active_counts,
            })

        summary = dict(legacy["summary"])
        summary.update({
            "online_devices": house["home"]["available_devices"],
            "offline_devices": house["home"]["unavailable_devices"],
            "house_status": house["home"]["status"],
        })

        result = dict(legacy)
        result["summary"] = summary
        result["rooms"] = rooms
        result["recent_activity"] = house["recent_activity"]
        result["generated_at"] = house["generated_at"]
        result["source"] = "house_model"
        context = getattr(self.core, "context", None)
        result["context"] = context.snapshot() if context is not None else {"home":{"status":"unknown","summary":"正在更新家庭状态。"},"rooms":[]}
        feed = getattr(self.core, "feed", None)
        if feed is None:
            result["feed"] = []
        else:
            result["feed"] = feed.snapshot(
                limit=6,
                include_system=False,
            )
        return result

    def house_room_payload(self, room_id):
        if self.core is None:
            return self.dashboard.room(room_id)

        house = self.core.house.snapshot()

        for room in house["rooms"]:
            if room["id"] == room_id:
                return {
                    "id": room["id"],
                    "name": room["name"],
                    "area": room["area"],
                    "order": room["order"],
                    "status": room["status"],
                    "device_count": room["device_count"],
                    "available_devices": room["available_devices"],
                    "unavailable_devices": room["unavailable_devices"],
                    "active_devices": room["active_devices"],
                    "last_activity": room["last_activity"],
                    "devices": room["devices"],
                    "source": "house_model",
                }

        return None

    def feed_payload(self):
        if self.core is None:
            return {
                "items": [],
                "count": 0,
            }

        items = self.core.feed.snapshot(
            limit=20,
            include_system=False,
        )

        return {
            "items": items,
            "count": len(items),
        }

    def context_payload(self):
        context = getattr(self.core, "context", None) if self.core is not None else None
        if context is None:
            return {
                "generated_at": None,
                "home": {
                    "name": self.config["home"]["home"]["name"],
                    "status": "unknown",
                    "summary": "正在更新家庭状态。",
                },
                "rooms": [],
            }
        return context.snapshot()

    def home_events_payload(self):
        bus = getattr(self.core, "home_events", None) if self.core is not None else None
        if bus is None:
            return {
                "stats": {
                    "history_count": 0,
                    "subscriber_groups": 0,
                    "subscriber_count": 0,
                },
                "events": [],
            }
        return {
            "stats": bus.stats(),
            "events": bus.snapshot(limit=50),
        }

    def rooms_payload(self):
        return [
            {
                "id": room.id,
                "name": room.name,
                "area": room.area,
                "order": room.order,
                "device_count": len(self.devices.by_room(room.id)),
            }
            for room in self.rooms.all()
        ]

    def devices_payload(self):
        result = []
        snapshot = self.states.snapshot()

        for device in self.devices.all():
            state = snapshot[device.id]
            result.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "room": device.room,
                    "type": device.type,
                    "adapter": device.adapter,
                    "capabilities": device.capabilities,
                    "available": state.available,
                    "state": state.state,
                    "attributes": state.attributes,
                    "updated_at": state.updated_at,
                }
            )

        return result

    def state_payload(self):
        return {
            device_id: {
                "device_id": state.device_id,
                "available": state.available,
                "state": state.state,
                "attributes": state.attributes,
                "updated_at": state.updated_at,
            }
            for device_id, state in self.states.snapshot().items()
        }

    def dashboard_payload(self):
        """Backward-compatible alias used by v0.2 API tests."""
        devices = self.devices_payload()

        lights_on = sum(
            1
            for device in devices
            if device["type"] == "light"
            and device["state"] == "on"
        )
        climate_on = sum(
            1
            for device in devices
            if device["type"] == "climate"
            and device["state"] not in ("off", "unknown")
        )
        curtains_active = sum(
            1
            for device in devices
            if device["type"] == "curtain"
            and device["state"] in (
                "opening",
                "closing",
                "stopped",
            )
        )

        return {
            "summary": {
                "lights_on": lights_on,
                "climate_on": climate_on,
                "curtains_active": curtains_active,
                "device_count": len(devices),
                "room_count": len(self.rooms.all()),
            },
            "rooms": self.rooms_payload(),
            "today_events": [],
        }


def make_handler(app, web_root: Path):
    class Handler(SimpleHTTPRequestHandler):
        server_version = "SmartScreenOS/0.4.2"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_root), **kwargs)

        def _write_json(self, payload, status=200):
            raw = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")

            self.send_response(status)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            routes = {
                "/api/v1/system": app.system_payload,
                "/api/v1/health": app.health_payload,
                "/api/v1/events": app.events_payload,
                "/api/v1/house": app.house_payload,
                "/api/v1/feed": app.feed_payload,
                "/api/v1/context": app.context_payload,
                "/api/v1/home-events": app.home_events_payload,
                "/api/v1/rooms": app.rooms_payload,
                "/api/v1/devices": app.devices_payload,
                "/api/v1/state": app.state_payload,
                "/api/v1/dashboard/home": app.house_home_payload,
            }

            function = routes.get(path)
            if function is not None:
                self._write_json(success(function()))
                return

            if path == "/api/v1/dashboard/room":
                room_id = parse_qs(parsed.query).get("id", [""])[0]
                payload = app.house_room_payload(room_id)

                if payload is None:
                    self._write_json(
                        error("unknown_room", "Room was not found."),
                        404,
                    )
                    return

                self._write_json(success(payload))
                return

            super().do_GET()

        def do_POST(self):
            parsed = urlparse(self.path)

            if not (
                parsed.path.startswith("/api/v1/devices/")
                and parsed.path.endswith("/commands")
            ):
                self._write_json(
                    error("not_found", "API endpoint was not found."),
                    404,
                )
                return

            if app.core is None:
                self._write_json(
                    error(
                        "command_unavailable",
                        "Command handling is unavailable in this context.",
                    ),
                    503,
                )
                return

            device_id = parsed.path[
                len("/api/v1/devices/") : -len("/commands")
            ].strip("/")

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")

            try:
                body = json.loads(raw)
                command = str(body["command"])
                value = body.get("value")
                app.core.command(device_id, command, value)
            except Exception as exc:
                self._write_json(
                    error("command_failed", str(exc)),
                    400,
                )
                return

            self._write_json(
                success({
                    "accepted": True,
                    "device_id": device_id,
                    "command": command,
                })
            )

        def log_message(self, format, *args):
            print("[HTTP]", format % args)

    return Handler


def run_api(app, host, port, web_root):
    server = ThreadingHTTPServer(
        (host, port),
        make_handler(app, web_root),
    )

    print("")
    print("========================================")
    print("SmartScreen OS Device Model v0.4.2")
    print("========================================")
    print("Dashboard:", f"http://127.0.0.1:{port}/")
    print("System   :", f"http://127.0.0.1:{port}/api/v1/system")
    print("========================================")
    print("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Stopping development server...")
    finally:
        server.server_close()

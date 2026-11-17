"""Configuration-driven dashboard view models."""

from __future__ import annotations


class DashboardEngine:
    def __init__(self, config, rooms, devices, states) -> None:
        self.config = config
        self.rooms = rooms
        self.devices = devices
        self.states = states

    def _dashboard_options(self):
        dashboard_root = self.config.get("dashboard", {})
        dashboard = dashboard_root.get("dashboard", {})

        return {
            "title": dashboard.get("title", "SmartScreen OS"),
            "refresh_seconds": int(dashboard.get("refresh_seconds", 5)),
            "theme": dashboard.get("theme", "dark"),
            "home_sections": list(
                dashboard.get(
                    "home_sections",
                    ["system", "summary", "rooms"],
                )
            ),
            "room_card": dict(
                dashboard.get(
                    "room_card",
                    {
                        "show_device_count": True,
                        "show_area": True,
                    },
                )
            ),
        }

    def _home_dashboard_options(self):
        root = self.config.get("home_dashboard", {})
        home_dashboard = root.get("home_dashboard", {})

        return {
            "family_name": home_dashboard.get(
                "family_name",
                self.config["home"]["home"].get("name", "SmartScreen Home"),
            ),
            "subtitle": home_dashboard.get(
                "subtitle",
                "智能家庭中心",
            ),
            "weather": dict(
                home_dashboard.get(
                    "weather",
                    {
                        "temperature": "--",
                        "condition": "暂无天气",
                        "air_quality": "--",
                        "source": "fallback",
                    },
                )
            ),
            "today_events": list(
                home_dashboard.get("today_events", [])
            ),
        }

    def home(self):
        system = self.config["system"]["system"]
        home = self.config["home"]["home"]
        dashboard = self._dashboard_options()
        home_dashboard = self._home_dashboard_options()

        return {
            "title": dashboard["title"],
            "family_name": home_dashboard["family_name"],
            "subtitle": home_dashboard["subtitle"],
            "home_name": home["name"],
            "version": system["version"],
            "refresh_seconds": dashboard["refresh_seconds"],
            "theme": dashboard["theme"],
            "summary": self._summary(),
            "rooms": self._room_cards(),
            "weather": home_dashboard["weather"],
            "today_events": home_dashboard["today_events"],
        }

    def room(self, room_id):
        selected = None
        for room in self.rooms.all():
            if room.id == room_id:
                selected = room
                break

        if selected is None:
            return None

        state_snapshot = self.states.snapshot()
        devices = []

        for device in self.devices.by_room(room_id):
            state = state_snapshot[device.id]
            devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "adapter": device.adapter,
                    "capabilities": device.capabilities,
                    "available": state.available,
                    "state": state.state,
                    "attributes": state.attributes,
                    "updated_at": state.updated_at,
                }
            )

        return {
            "id": selected.id,
            "name": selected.name,
            "area": selected.area,
            "order": selected.order,
            "devices": devices,
        }

    def _summary(self):
        snapshot = self.states.snapshot()
        devices = self.devices.all()

        lights_on = 0
        climate_on = 0
        curtain_active = 0
        online_devices = 0

        for device in devices:
            state_obj = snapshot[device.id]
            state = state_obj.state

            if state_obj.available:
                online_devices += 1

            if device.type == "light" and state == "on":
                lights_on += 1
            elif device.type == "climate" and state not in ("off", "unknown"):
                climate_on += 1
            elif device.type == "curtain" and state in (
                "opening",
                "closing",
                "stopped",
                "open",
            ):
                curtain_active += 1

        return {
            "room_count": len(self.rooms.all()),
            "device_count": len(devices),
            "online_devices": online_devices,
            "lights_on": lights_on,
            "climate_on": climate_on,
            "curtains_active": curtain_active,
        }

    def _room_cards(self):
        cards = []
        snapshot = self.states.snapshot()

        for room in self.rooms.all():
            room_devices = self.devices.by_room(room.id)
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

            for device in room_devices:
                if device.type in type_counts:
                    type_counts[device.type] += 1

                state = snapshot[device.id].state

                if device.type == "light" and state == "on":
                    active_counts["light"] += 1
                elif device.type == "curtain" and state in (
                    "open",
                    "opening",
                    "closing",
                    "stopped",
                ):
                    active_counts["curtain"] += 1
                elif device.type == "climate" and state not in (
                    "off",
                    "unknown",
                ):
                    active_counts["climate"] += 1
                elif device.type == "occupancy" and state == "on":
                    active_counts["occupancy"] += 1

            cards.append(
                {
                    "id": room.id,
                    "name": room.name,
                    "area": room.area,
                    "order": room.order,
                    "device_count": len(room_devices),
                    "type_counts": type_counts,
                    "active_counts": active_counts,
                }
            )

        return cards

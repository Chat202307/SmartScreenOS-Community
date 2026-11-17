import unittest

from src.smartscreen.dashboard import DashboardEngine
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10),
            Room("study", "书房", "private_area", 20),
        ])

        self.devices = DeviceRegistry([
            Device(
                "living.light",
                "客厅灯",
                "living",
                "light",
                "mqtt",
            )
        ], self.rooms)

        self.states = StateStore()
        self.states.initialize("living.light")

        self.config = {
            "system": {
                "system": {
                    "version": "0.3.0-dev",
                }
            },
            "home": {
                "home": {
                    "name": "测试家庭",
                }
            },
            "dashboard": {
                "dashboard": {
                    "title": "SmartScreen OS",
                    "refresh_seconds": 5,
                    "theme": "dark",
                    "home_sections": [
                        "system",
                        "summary",
                        "rooms",
                    ],
                    "room_card": {
                        "show_device_count": True,
                        "show_area": True,
                    },
                }
            },
        }

        self.engine = DashboardEngine(
            self.config,
            self.rooms,
            self.devices,
            self.states,
        )

    def test_home_uses_configuration(self):
        home = self.engine.home()
        self.assertEqual(home["home_name"], "测试家庭")
        self.assertEqual(len(home["rooms"]), 2)

    def test_room_is_generated_from_registry(self):
        room = self.engine.room("living")
        self.assertEqual(room["name"], "客厅")
        self.assertEqual(len(room["devices"]), 1)

    def test_unknown_room_returns_none(self):
        self.assertIsNone(self.engine.room("missing"))


if __name__ == "__main__":
    unittest.main()

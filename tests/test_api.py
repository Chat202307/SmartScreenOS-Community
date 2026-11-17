import unittest

from src.smartscreen.api import ApiApplication
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.rooms = RoomRegistry([
            Room("living", "客厅", "public", 10),
        ])
        self.devices = DeviceRegistry([
            Device(
                "living.light",
                "客厅灯",
                "living",
                "light",
                "mqtt",
                ["turn_on", "turn_off"],
            )
        ], self.rooms)
        self.states = StateStore()
        self.states.initialize("living.light")
        self.config = {
            "system": {
                "system": {
                    "name": "SmartScreen OS",
                    "version": "0.2.0-dev",
                    "development_port": 8081,
                    "stable_port": 8080,
                }
            },
            "home": {
                "home": {
                    "name": "测试家庭",
                }
            },
        }
        self.app = ApiApplication(
            self.config,
            self.rooms,
            self.devices,
            self.states,
        )

    def test_rooms_payload(self):
        rooms = self.app.rooms_payload()
        self.assertEqual(rooms[0]["name"], "客厅")
        self.assertEqual(rooms[0]["device_count"], 1)

    def test_dashboard_counts(self):
        payload = self.app.dashboard_payload()
        self.assertEqual(payload["summary"]["room_count"], 1)
        self.assertEqual(payload["summary"]["device_count"], 1)


if __name__ == "__main__":
    unittest.main()

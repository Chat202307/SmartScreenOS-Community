import unittest

from src.smartscreen.dashboard import DashboardEngine
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class HomeDashboardTests(unittest.TestCase):
    def test_home_dashboard_contains_family_data(self):
        rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10)
        ])

        devices = DeviceRegistry([
            Device(
                "living.light",
                "客厅灯",
                "living",
                "light",
                "mqtt",
                ["turn_on", "turn_off"],
            )
        ], rooms)

        states = StateStore()
        states.initialize("living.light")

        config = {
            "system": {"system": {"version": "0.7.0-dev"}},
            "home": {"home": {"name": "测试家庭"}},
            "dashboard": {"dashboard": {}},
            "home_dashboard": {
                "home_dashboard": {
                    "family_name": "Test Family",
                    "subtitle": "智能家庭中心",
                    "weather": {
                        "temperature": 27,
                        "condition": "晴",
                        "air_quality": "优",
                    },
                    "today_events": [],
                }
            },
        }

        engine = DashboardEngine(
            config,
            rooms,
            devices,
            states,
        )

        payload = engine.home()

        self.assertEqual(payload["family_name"], "Test Family")
        self.assertEqual(payload["summary"]["room_count"], 1)
        self.assertEqual(payload["rooms"][0]["type_counts"]["light"], 1)

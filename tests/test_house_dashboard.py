import unittest

from src.smartscreen.api import ApiApplication
from src.smartscreen.events import EventBus
from src.smartscreen.house import HouseModel
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class FakeAdapters:
    def health(self):
        return {}


class FakeCore:
    def __init__(self, house):
        self.house = house
        self.adapters = FakeAdapters()
        self.events = EventBus()


class HouseDashboardTests(unittest.TestCase):
    def setUp(self):
        rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10),
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
        states.update(
            "living.light",
            available=True,
            state="on",
            attributes={},
        )

        bus = EventBus()
        house = HouseModel(
            {"home": {"name": "测试家庭"}},
            rooms,
            devices,
            states,
            bus,
        )

        config = {
            "system": {
                "system": {
                    "name": "SmartScreen OS",
                    "version": "0.9.3-dev",
                    "development_port": 8081,
                    "stable_port": 8080,
                }
            },
            "home": {
                "home": {
                    "name": "测试家庭",
                }
            },
            "dashboard": {
                "dashboard": {}
            },
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

        self.app = ApiApplication(
            config,
            rooms,
            devices,
            states,
            FakeCore(house),
        )

    def test_home_uses_house_model(self):
        payload = self.app.house_home_payload()

        self.assertEqual(payload["source"], "house_model")
        self.assertEqual(payload["rooms"][0]["status"], "active")
        self.assertEqual(payload["rooms"][0]["active_devices"], 1)

    def test_room_uses_house_model(self):
        payload = self.app.house_room_payload("living")

        self.assertEqual(payload["source"], "house_model")
        self.assertEqual(payload["name"], "客厅")
        self.assertEqual(payload["status"], "active")

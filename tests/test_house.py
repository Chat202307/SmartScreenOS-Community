import unittest

from src.smartscreen.events import EventBus
from src.smartscreen.house import HouseModel
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class HouseModelTests(unittest.TestCase):
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
                ["turn_on", "turn_off"],
            ),
            Device(
                "living.climate",
                "客厅空调",
                "living",
                "climate",
                "mqtt",
                ["turn_off", "set_mode"],
            ),
        ], self.rooms)

        self.states = StateStore()
        self.states.initialize("living.light")
        self.states.initialize("living.climate")

        self.bus = EventBus()
        self.house = HouseModel(
            {"home": {"name": "测试家庭"}},
            self.rooms,
            self.devices,
            self.states,
            self.bus,
        )

    def test_snapshot_contains_rooms(self):
        payload = self.house.snapshot()
        self.assertEqual(payload["home"]["room_count"], 2)
        self.assertEqual(payload["rooms"][0]["name"], "客厅")

    def test_active_room(self):
        self.states.update(
            "living.light",
            available=True,
            state="on",
            attributes={},
        )
        self.states.update(
            "living.climate",
            available=True,
            state="off",
            attributes={},
        )

        payload = self.house.snapshot()
        living = payload["rooms"][0]

        self.assertEqual(living["status"], "active")
        self.assertEqual(living["active_devices"], 1)

    def test_event_creates_recent_activity(self):
        self.bus.publish(
            "device.state_changed",
            source="test",
            payload={
                "device_id": "living.light",
                "available": True,
                "state": "on",
                "attributes": {},
            },
        )

        payload = self.house.snapshot()

        self.assertEqual(len(payload["recent_activity"]), 1)
        self.assertEqual(
            payload["recent_activity"][0]["device_id"],
            "living.light",
        )

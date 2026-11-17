import unittest

from src.smartscreen.events import EventBus
from src.smartscreen.house import HouseModel
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry
from src.smartscreen.state_store import StateStore


class HouseDedupTests(unittest.TestCase):
    def test_only_changed_events_enter_activity(self):
        rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10),
        ])

        devices = DeviceRegistry([
            Device(
                "living.climate",
                "客厅空调",
                "living",
                "climate",
                "mqtt",
                ["turn_off", "set_mode"],
            )
        ], rooms)

        states = StateStore()
        states.initialize("living.climate")
        bus = EventBus()

        house = HouseModel(
            {"home": {"name": "测试家庭"}},
            rooms,
            devices,
            states,
            bus,
        )

        bus.publish(
            "device.state_seen",
            source="test",
            payload={
                "device_id": "living.climate",
                "state": "cool",
            },
        )

        self.assertEqual(
            len(house.snapshot()["recent_activity"]),
            0,
        )

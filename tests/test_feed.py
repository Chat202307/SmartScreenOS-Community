import unittest

from src.smartscreen.events import EventBus
from src.smartscreen.feed import FeedGenerator
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry


class FeedGeneratorTests(unittest.TestCase):
    def setUp(self):
        rooms = RoomRegistry([
            Room("living", "客厅", "public_area", 10),
        ])

        self.devices = DeviceRegistry([
            Device(
                "living.light",
                "客厅主灯",
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
        ], rooms)

        self.bus = EventBus()
        self.feed = FeedGenerator(
            self.devices,
            self.bus,
        )

    def test_initial_state_is_not_feed(self):
        self.bus.publish(
            "device.state_changed",
            source="test",
            payload={
                "device_id": "living.light",
                "previous": None,
                "current": {
                    "available": True,
                    "state": "off",
                    "attributes": {},
                },
            },
        )

        self.assertEqual(self.feed.snapshot(), [])

    def test_light_change_creates_feed(self):
        self.bus.publish(
            "device.state_changed",
            source="test",
            payload={
                "device_id": "living.light",
                "previous": {
                    "available": True,
                    "state": "off",
                    "attributes": {},
                },
                "current": {
                    "available": True,
                    "state": "on",
                    "attributes": {},
                },
            },
        )

        items = self.feed.snapshot()

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["text"], "已开启")
        self.assertEqual(items[0]["kind"], "home")

    def test_temperature_change_creates_feed(self):
        self.bus.publish(
            "device.state_changed",
            source="test",
            payload={
                "device_id": "living.climate",
                "previous": {
                    "available": True,
                    "state": "cool",
                    "attributes": {
                        "target_temperature": 24,
                    },
                },
                "current": {
                    "available": True,
                    "state": "cool",
                    "attributes": {
                        "target_temperature": 25,
                    },
                },
            },
        )

        items = self.feed.snapshot()

        self.assertEqual(
            items[0]["text"],
            "设定温度调整为 25℃",
        )

    def test_system_events_are_hidden_by_default(self):
        self.bus.publish(
            "adapter.connected",
            source="mqtt",
            payload={"adapter": "mqtt"},
        )

        self.assertEqual(self.feed.snapshot(), [])
        self.assertEqual(
            len(self.feed.snapshot(include_system=True)),
            1,
        )

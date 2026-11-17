import unittest
from src.smartscreen.home_event import HomeEvent

class HomeEventTests(unittest.TestCase):
    def test_create_and_serialize(self):
        event = HomeEvent.create(
            "device.state_changed",
            source="mqtt",
            room_id="living",
            device_id="living.light",
            payload={"state": "on"},
        )
        data = event.to_dict()
        self.assertEqual(data["event_type"], "device.state_changed")
        self.assertEqual(data["room_id"], "living")
        self.assertEqual(data["payload"]["state"], "on")

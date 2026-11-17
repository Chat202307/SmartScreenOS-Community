import unittest
from src.smartscreen.models import Room, Device
from src.smartscreen.registry import RoomRegistry, DeviceRegistry, RegistryError

class RegistryTests(unittest.TestCase):
    def test_unknown_room(self):
        rooms=RoomRegistry([Room("living","客厅","public",10)])
        with self.assertRaises(RegistryError):
            DeviceRegistry([Device("x","X","missing","light","mqtt")],rooms)
    def test_filter(self):
        rooms=RoomRegistry([Room("living","客厅","public",10)])
        devices=DeviceRegistry([Device("living.light","灯","living","light","mqtt")],rooms)
        self.assertEqual(len(devices.by_room("living")),1)

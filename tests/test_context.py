import unittest
from src.smartscreen.context import ContextEngine

class FakeHouse:
    def snapshot(self):
        return {
            "generated_at":"2026-08-02T01:00:00+00:00",
            "home":{"name":"测试家庭","status":"healthy","unavailable_devices":0},
            "rooms":[{
                "id":"living","name":"客厅","status":"active",
                "device_count":4,"available_devices":4,"unavailable_devices":0,
                "active_devices":3,"last_activity":None,
                "devices":[
                    {"id":"l","name":"主灯","type":"light","available":True,"state":"on","attributes":{}},
                    {"id":"c","name":"窗帘","type":"curtain","available":True,"state":"open","attributes":{}},
                    {"id":"a","name":"空调","type":"climate","available":True,"state":"cool","attributes":{"current_temperature":24}},
                    {"id":"o","name":"人体","type":"occupancy","available":True,"state":"on","attributes":{}},
                ]
            }]
        }

class ContextEngineTests(unittest.TestCase):
    def test_room_context(self):
        room = ContextEngine(FakeHouse()).snapshot()["rooms"][0]
        self.assertEqual(room["presence"],"occupied")
        self.assertEqual(room["comfort"],"good")
        self.assertEqual(room["lighting"],"bright")
        self.assertEqual(room["climate"],"cool")
        self.assertEqual(room["privacy"],"open")
        self.assertEqual(room["activity"],"active")
        self.assertEqual(room["temperature"],24)

    def test_room_lookup(self):
        engine = ContextEngine(FakeHouse())
        self.assertIsNotNone(engine.room("living"))
        self.assertIsNone(engine.room("missing"))

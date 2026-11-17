import unittest
from src.smartscreen.connection import ConnectionManager

class ConnectionTests(unittest.TestCase):
    def test_lifecycle_and_messages(self):
        manager=ConnectionManager()
        manager.register("mqtt")
        manager.set_state("mqtt","connecting")
        manager.set_state("mqtt","connected")
        manager.mark_message("mqtt")
        data=manager.snapshot()
        self.assertEqual(data["connections"]["mqtt"]["state"],"connected")
        self.assertEqual(data["connections"]["mqtt"]["message_count"],1)
        self.assertGreaterEqual(len(data["events"]),2)

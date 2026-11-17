import unittest

from src.smartscreen.events import EventBus


class EventBusTests(unittest.TestCase):
    def test_publish_and_subscribe(self):
        bus = EventBus()
        received = []

        bus.subscribe(
            "device.state_changed",
            lambda event: received.append(event),
        )

        event = bus.publish(
            "device.state_changed",
            source="test",
            payload={
                "device_id": "living.light",
                "state": "on",
            },
        )

        self.assertEqual(event.name, "device.state_changed")
        self.assertEqual(len(received), 1)
        self.assertEqual(
            received[0].payload["state"],
            "on",
        )

    def test_wildcard_subscriber(self):
        bus = EventBus()
        received = []

        bus.subscribe("*", lambda event: received.append(event))
        bus.publish("core.started", source="core", payload={})
        bus.publish("adapter.connected", source="mqtt", payload={})

        self.assertEqual(len(received), 2)

    def test_history_limit(self):
        bus = EventBus(history_limit=2)

        bus.publish("event.1", source="test")
        bus.publish("event.2", source="test")
        bus.publish("event.3", source="test")

        recent = bus.recent(10)

        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0].name, "event.3")
        self.assertEqual(recent[1].name, "event.2")

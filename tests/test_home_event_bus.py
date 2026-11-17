import unittest
from src.smartscreen.home_event import HomeEvent
from src.smartscreen.home_event_bus import HomeEventBus

class HomeEventBusTests(unittest.TestCase):
    def test_publish_and_snapshot(self):
        bus = HomeEventBus()
        bus.publish(HomeEvent.create('home.device.state_changed', source='test', room_id='living', device_id='living.light', payload={'state':'on'}))
        snapshot = bus.snapshot()
        self.assertEqual(len(snapshot), 1)
        self.assertEqual(snapshot[0]['event_type'], 'home.device.state_changed')

    def test_subscriber_receives_event(self):
        bus = HomeEventBus()
        received = []
        bus.subscribe('home.device.state_changed', received.append)
        bus.publish(HomeEvent.create('home.device.state_changed', source='test'))
        self.assertEqual(len(received), 1)

    def test_wildcard_subscriber(self):
        bus = HomeEventBus()
        received = []
        bus.subscribe('*', received.append)
        bus.publish(HomeEvent.create('home.adapter.connected', source='mqtt'))
        self.assertEqual(len(received), 1)

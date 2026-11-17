import unittest
from src.smartscreen.home_event_mapper import HomeEventMapper
from src.smartscreen.models import Device, Room
from src.smartscreen.registry import DeviceRegistry, RoomRegistry

class HomeEventMapperTests(unittest.TestCase):
    def test_device_state_mapping(self):
        rooms = RoomRegistry([Room('living','客厅','public_area',10)])
        devices = DeviceRegistry([Device('living.light','主灯','living','light','mqtt',['turn_on','turn_off'])], rooms)
        mapper = HomeEventMapper(devices)
        event = mapper.from_device_state('living.light', True, 'on', {}, previous={'state':'off'}, current={'state':'on'})
        self.assertEqual(event.event_type, 'home.device.state_changed')
        self.assertEqual(event.room_id, 'living')
        self.assertEqual(event.device_id, 'living.light')

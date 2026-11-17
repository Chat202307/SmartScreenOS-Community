import unittest


class DeviceCardContractTests(unittest.TestCase):
    def test_light_contract(self):
        device = {
            "type": "light",
            "state": "on",
            "available": True,
            "attributes": {},
        }
        self.assertEqual(device["type"], "light")
        self.assertTrue(device["available"])

    def test_climate_contract(self):
        device = {
            "type": "climate",
            "state": "cool",
            "available": True,
            "attributes": {
                "target_temperature": 24,
                "current_temperature": 26,
                "fan_mode": "low",
            },
        }
        self.assertEqual(
            device["attributes"]["target_temperature"],
            24,
        )

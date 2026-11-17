import unittest

from src.smartscreen.device_types import (
    DeviceTypeError,
    validate_device_type,
)


class DeviceTypeTests(unittest.TestCase):
    def test_valid_light_capability(self):
        validate_device_type("light", ["turn_on", "turn_off"])

    def test_invalid_capability_is_rejected(self):
        with self.assertRaises(DeviceTypeError):
            validate_device_type("light", ["open"])

    def test_unknown_type_is_rejected(self):
        with self.assertRaises(DeviceTypeError):
            validate_device_type("unknown", [])

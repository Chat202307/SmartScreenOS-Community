import json
import unittest

from src.smartscreen.adapters.mqtt import MqttAdapter


class MqttAdapterNormalizeTests(unittest.TestCase):
    def test_light(self):
        result = MqttAdapter._normalize("light", "ON")
        self.assertEqual(result["state"], "on")

    def test_curtain(self):
        result = MqttAdapter._normalize("curtain", "STOPPED")
        self.assertEqual(result["state"], "stopped")

    def test_climate_off_overrides_mode(self):
        raw = json.dumps({
            "power": "OFF",
            "mode": "COOL",
            "temp_set": 24,
            "temp_room": 26,
            "fan": "LOW",
        })

        result = MqttAdapter._normalize("climate", raw)
        self.assertEqual(result["state"], "off")
        self.assertEqual(
            result["attributes"]["target_temperature"],
            24,
        )

    def test_climate_cool(self):
        raw = json.dumps({
            "power": "ON",
            "mode": "COOL",
            "temp_set": 23,
            "temp_room": 24,
            "fan": "UNKNOWN",
            "fan_raw": 0,
        })

        result = MqttAdapter._normalize("climate", raw)
        self.assertEqual(result["state"], "cool")
        self.assertEqual(
            result["attributes"]["current_temperature"],
            24,
        )

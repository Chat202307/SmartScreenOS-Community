import unittest

from src.smartscreen.state_change import StateChangeDetector


class StateChangeDetectorTests(unittest.TestCase):
    def test_first_state_is_change(self):
        detector = StateChangeDetector()

        result = detector.evaluate(
            "living.light",
            True,
            "off",
            {},
        )

        self.assertTrue(result["changed"])
        self.assertIsNone(result["previous"])

    def test_identical_state_is_not_change(self):
        detector = StateChangeDetector()

        detector.evaluate(
            "living.climate",
            True,
            "cool",
            {
                "target_temperature": 24,
                "current_temperature": 25,
            },
        )

        result = detector.evaluate(
            "living.climate",
            True,
            "cool",
            {
                "target_temperature": 24,
                "current_temperature": 25,
            },
        )

        self.assertFalse(result["changed"])

    def test_attribute_change_is_detected(self):
        detector = StateChangeDetector()

        detector.evaluate(
            "living.climate",
            True,
            "cool",
            {"current_temperature": 25},
        )

        result = detector.evaluate(
            "living.climate",
            True,
            "cool",
            {"current_temperature": 26},
        )

        self.assertTrue(result["changed"])
        self.assertEqual(
            result["previous"]["attributes"]["current_temperature"],
            25,
        )
        self.assertEqual(
            result["current"]["attributes"]["current_temperature"],
            26,
        )

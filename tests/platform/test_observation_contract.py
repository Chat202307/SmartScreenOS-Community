import unittest

from src.smartscreen_platform.contracts import Observation

class ObservationContractTests(unittest.TestCase):
    def test_temperature_observation(self):
        item = Observation.create(
            parameter="temperature",
            value=29,
            unit="degC",
            confidence=0.98,
            location_id="living",
            provenance={"provider": "runtime"},
        )

        data = item.to_dict()

        self.assertEqual(data["parameter"], "temperature")
        self.assertEqual(data["value"], 29)
        self.assertEqual(data["location_id"], "living")
        self.assertEqual(data["provenance"]["provider"], "runtime")

    def test_presence_observation_is_device_independent(self):
        item = Observation.create(
            parameter="presence",
            value=True,
            confidence=0.92,
            location_id="living",
        )

        self.assertTrue(item.value)
        self.assertNotIn("device_id", item.to_dict())

    def test_confidence_range_is_enforced(self):
        with self.assertRaises(ValueError):
            Observation.create(
                parameter="temperature",
                value=29,
                confidence=1.2,
            )

def test_observation_has_unique_stable_identity():
    first = Observation.create(
        parameter="temperature",
        value=25.8,
        unit="degC",
        provenance={"provider": "test"},
    )

    second = Observation.create(
        parameter="temperature",
        value=25.8,
        unit="degC",
        provenance={"provider": "test"},
    )

    assert isinstance(first.observation_id, str)
    assert first.observation_id
    assert isinstance(second.observation_id, str)
    assert second.observation_id

    assert first.observation_id != second.observation_id

    first_id = first.observation_id
    assert first.observation_id == first_id

    serialized = first.to_dict()
    assert serialized["observation_id"] == first.observation_id

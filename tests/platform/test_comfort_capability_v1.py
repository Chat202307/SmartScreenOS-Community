import unittest

from src.smartscreen_platform.capabilities.comfort import (
    ComfortCapability,
)
from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.household_state import HouseholdStateEngine
from src.smartscreen_platform.interpretation import (
    IlluminanceInterpreter,
    ThermalInterpreter,
)
from src.smartscreen_platform.knowledge import StaticKnowledge


class ComfortCapabilityV1Tests(unittest.TestCase):
    def setUp(self):
        self.knowledge = StaticKnowledge(
            global_values={
                "thermal_preferred_low": 22,
                "thermal_preferred_high": 27,
                "thermal_hot_threshold": 30,
                "thermal_cold_threshold": 18,
            }
        )
        self.capability = ComfortCapability()

    def _thermal(self, temperature):
        observations = [
            Observation.create(
                "temperature",
                temperature,
                unit="degC",
                confidence=0.98,
                location_id="living",
            )
        ]
        result = ThermalInterpreter().interpret(
            observations,
            knowledge=self.knowledge,
        )
        return observations, result

    def test_complete_comfort_chain(self):
        observations, interpretations = self._thermal(29)
        humidity = Observation.create(
            "humidity",
            75,
            unit="percent",
            confidence=0.90,
            location_id="living",
        )
        observations += [
            humidity,
            Observation.create(
                "illuminance",
                200,
                unit="lux",
                confidence=0.95,
                location_id="living",
            ),
            Observation.create(
                "noise_level",
                40,
                unit="dBA",
                confidence=0.95,
                location_id="living",
            ),
        ]

        patch = self.capability.evaluate(
            interpretations,
            observations=observations,
            knowledge=self.knowledge,
        )[0]

        engine = HouseholdStateEngine()
        entry = engine.apply(patch)

        self.assertEqual(entry.target, "comfort")
        self.assertEqual(entry.value["level"], "slightly_uncomfortable")
        self.assertIn(
            humidity.observation_id,
            entry.evidence_refs,
        )
        self.assertNotIn(
            "humidity",
            entry.evidence_refs,
        )

    def test_incomplete_information_produces_no_comfort(self):
        observations, interpretations = self._thermal(29)

        patches = self.capability.evaluate(
            interpretations,
            observations=observations,
        )

        self.assertEqual(patches, [])





if __name__ == "__main__":
    unittest.main()


def test_comfort_evidence_refs_use_observation_identity():
    temperature = Observation.create(
        "temperature",
        29,
        unit="degC",
        confidence=0.98,
        location_id="living",
    )

    humidity = Observation.create(
        "humidity",
        75,
        unit="percent",
        confidence=0.90,
        location_id="living",
    )

    illuminance = Observation.create(
        "illuminance",
        200,
        unit="lux",
        confidence=0.95,
        location_id="living",
    )

    noise = Observation.create(
        "noise_level",
        40,
        unit="dBA",
        confidence=0.95,
        location_id="living",
    )

    observations = [
        temperature,
        humidity,
        illuminance,
        noise,
    ]

    interpretations = []

    interpretations.extend(
        ThermalInterpreter().interpret(
            observations,
        )
    )

    interpretations.extend(
        IlluminanceInterpreter().interpret(
            observations,
        )
    )

    patch = ComfortCapability().evaluate(
        interpretations,
        observations=observations,
    )[0]

    expected = {
        temperature.observation_id,
        humidity.observation_id,
        illuminance.observation_id,
        noise.observation_id,
    }

    assert set(patch.evidence_refs) == expected

    assert "temperature" not in patch.evidence_refs
    assert "humidity" not in patch.evidence_refs
    assert "illuminance" not in patch.evidence_refs
    assert "noise_level" not in patch.evidence_refs


def test_comfort_consumes_lighting_interpretation_without_raw_illuminance():
    from src.smartscreen_platform.contracts import (
        Interpretation,
    )

    temperature = Observation.create(
        "temperature",
        25,
        unit="degC",
        location_id="living",
    )

    humidity = Observation.create(
        "humidity",
        50,
        unit="percent",
        location_id="living",
    )

    thermal = ThermalInterpreter().interpret(
        [temperature]
    )[0]

    lighting = Interpretation.create(
        interpretation_type="lighting_state",
        name="lighting_state",
        value="dim",
        confidence=0.95,
        location_id="living",
        evidence_refs=[
            "observation:illuminance-1",
        ],
        expires_in_seconds=300,
    )

    patch = ComfortCapability().evaluate(
        [
            thermal,
            lighting,
        ],
        observations=[
            temperature,
            humidity,
        ],
    )[0]

    assert (
        patch.value["dimensions"]["lighting"]
        == "dim"
    )

    assert (
        "observation:illuminance-1"
        in patch.evidence_refs
    )


def test_comfort_uses_interpreted_lighting_thresholds_not_raw_lux():
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
    )

    knowledge = StaticKnowledge(
        location_values={
            "corridor": {
                "lighting_dim_below_lux": 50,
                "lighting_bright_above_lux": 500,
            }
        },
    )

    temperature = Observation.create(
        "temperature",
        25,
        unit="degC",
        location_id="corridor",
    )

    humidity = Observation.create(
        "humidity",
        50,
        unit="percent",
        location_id="corridor",
    )

    illuminance = Observation.create(
        "illuminance",
        60,
        unit="lux",
        confidence=0.95,
        location_id="corridor",
    )

    interpretations = []

    interpretations.extend(
        ThermalInterpreter().interpret(
            [temperature],
            knowledge=knowledge,
        )
    )

    interpretations.extend(
        IlluminanceInterpreter().interpret(
            [illuminance],
            knowledge=knowledge,
        )
    )

    patch = ComfortCapability().evaluate(
        interpretations,
        observations=[
            temperature,
            humidity,
            illuminance,
        ],
        knowledge=knowledge,
    )[0]

    assert (
        patch.value["dimensions"]["lighting"]
        == "comfortable"
    )

    assert (
        illuminance.observation_id
        in patch.evidence_refs
    )

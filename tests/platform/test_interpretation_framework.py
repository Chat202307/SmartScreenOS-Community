import unittest

from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.interpretation import (
    PresenceInterpreter,
    ThermalInterpreter,
)
from src.smartscreen_platform.knowledge import StaticKnowledge


class InterpretationFrameworkTests(unittest.TestCase):
    def test_thermal_interpretation_uses_knowledge(self):
        knowledge = StaticKnowledge(
            global_values={
                "thermal_preferred_low": 22,
                "thermal_preferred_high": 30,
                "thermal_hot_threshold": 33,
                "thermal_cold_threshold": 18,
            }
        )
        result = ThermalInterpreter().interpret([
            Observation.create(
                "temperature",
                29,
                unit="degC",
                location_id="living",
            )
        ], knowledge=knowledge)
        self.assertEqual(result[0].value, "comfortable")

    def test_presence_interpretation(self):
        result = PresenceInterpreter().interpret([
            Observation.create(
                "presence",
                True,
                location_id="living",
            ),
            Observation.create(
                "occupancy_count",
                3,
                location_id="living",
            ),
        ])
        self.assertEqual(result[0].name, "occupied")
        self.assertEqual(result[0].value, 3)

    def test_missing_required_observation_returns_empty(self):
        self.assertEqual(
            ThermalInterpreter().interpret([]),
            [],
        )


if __name__ == "__main__":
    unittest.main()


def test_interpretation_evidence_refs_use_observation_identity():
    temperature = Observation.create(
        "temperature",
        29,
        unit="degC",
        location_id="living",
    )

    humidity = Observation.create(
        "humidity",
        75,
        unit="percent",
        location_id="living",
    )

    result = ThermalInterpreter().interpret(
        [temperature, humidity]
    )

    assert len(result) == 1

    interpretation = result[0]

    assert interpretation.evidence_refs == [
        temperature.observation_id,
        humidity.observation_id,
    ]

    assert "temperature" not in interpretation.evidence_refs
    assert "humidity" not in interpretation.evidence_refs


def test_thermal_evidence_refs_only_include_consumed_observations():
    temperature = Observation.create(
        "temperature",
        29,
        unit="degC",
        location_id="living",
    )

    humidity = Observation.create(
        "humidity",
        75,
        unit="percent",
        location_id="living",
    )

    illuminance = Observation.create(
        "illuminance",
        200,
        unit="lux",
        location_id="living",
    )

    noise = Observation.create(
        "noise_level",
        40,
        unit="dBA",
        location_id="living",
    )

    result = ThermalInterpreter().interpret(
        [
            temperature,
            humidity,
            illuminance,
            noise,
        ]
    )

    assert result[0].evidence_refs == [
        temperature.observation_id,
        humidity.observation_id,
    ]

    assert illuminance.observation_id not in result[0].evidence_refs
    assert noise.observation_id not in result[0].evidence_refs


def test_presence_interpreter_derives_occupied_from_configured_motion_idle():
    motion = Observation.create(
        "motion_idle_seconds",
        0,
        unit="s",
        location_id="corridor",
        provenance={
            "provider": "home_assistant",
            "entity_id":
                "sensor.corridor_motion_idle",
        },
    )

    interpreter = PresenceInterpreter(
        source_policies=[
            {
                "entity_id":
                    "sensor.corridor_motion_idle",
                "location_id": "corridor",
                "parameter":
                    "motion_idle_seconds",
                "strategy":
                    "motion_idle_threshold",
                "settings": {
                    "occupied_below_seconds": 60,
                },
            }
        ]
    )

    result = interpreter.interpret(
        [motion]
    )

    assert len(result) == 1
    assert result[0].name == "occupied"
    assert result[0].value is None
    assert result[0].location_id == "corridor"
    assert result[0].evidence_refs == [
        motion.observation_id,
    ]


def test_presence_interpreter_derives_unoccupied_at_motion_threshold():
    motion = Observation.create(
        "motion_idle_seconds",
        60,
        unit="s",
        location_id="corridor",
        provenance={
            "provider": "home_assistant",
            "entity_id":
                "sensor.corridor_motion_idle",
        },
    )

    interpreter = PresenceInterpreter(
        source_policies=[
            {
                "entity_id":
                    "sensor.corridor_motion_idle",
                "location_id": "corridor",
                "parameter":
                    "motion_idle_seconds",
                "strategy":
                    "motion_idle_threshold",
                "settings": {
                    "occupied_below_seconds": 60,
                },
            }
        ]
    )

    result = interpreter.interpret(
        [motion]
    )

    assert len(result) == 1
    assert result[0].name == "unoccupied"
    assert result[0].value == 0
    assert result[0].location_id == "corridor"


def test_direct_presence_remains_authoritative_over_motion_policy():
    presence = Observation.create(
        "presence",
        True,
        location_id="corridor",
    )

    motion = Observation.create(
        "motion_idle_seconds",
        300,
        unit="s",
        location_id="corridor",
        provenance={
            "provider": "home_assistant",
            "entity_id":
                "sensor.corridor_motion_idle",
        },
    )

    interpreter = PresenceInterpreter(
        source_policies=[
            {
                "entity_id":
                    "sensor.corridor_motion_idle",
                "location_id": "corridor",
                "parameter":
                    "motion_idle_seconds",
                "strategy":
                    "motion_idle_threshold",
                "settings": {
                    "occupied_below_seconds": 60,
                },
            }
        ]
    )

    result = interpreter.interpret(
        [
            presence,
            motion,
        ]
    )

    assert len(result) == 1
    assert result[0].name == "occupied"
    assert result[0].evidence_refs == [
        presence.observation_id,
        motion.observation_id,
    ]


def test_unconfigured_motion_source_does_not_create_occupancy():
    motion = Observation.create(
        "motion_idle_seconds",
        0,
        unit="s",
        location_id="corridor",
        provenance={
            "provider": "home_assistant",
            "entity_id":
                "sensor.unknown_motion",
        },
    )

    interpreter = PresenceInterpreter(
        source_policies=[]
    )

    assert interpreter.interpret(
        [motion]
    ) == []


def test_illuminance_interpreter_reports_dim():
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
    )

    illuminance = Observation.create(
        "illuminance",
        45,
        unit="lux",
        confidence=0.95,
        location_id="corridor",
    )

    result = IlluminanceInterpreter().interpret(
        [illuminance]
    )

    assert len(result) == 1

    interpretation = result[0]

    assert (
        interpretation.interpretation_type
        == "lighting_state"
    )
    assert interpretation.name == "lighting_state"
    assert interpretation.value == "dim"
    assert interpretation.location_id == "corridor"
    assert interpretation.confidence == 0.95
    assert interpretation.evidence_refs == [
        illuminance.observation_id
    ]


def test_illuminance_interpreter_reports_comfortable():
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
    )

    illuminance = Observation.create(
        "illuminance",
        300,
        unit="lux",
        location_id="living",
    )

    result = IlluminanceInterpreter().interpret(
        [illuminance]
    )

    assert result[0].value == "comfortable"


def test_illuminance_interpreter_reports_bright():
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
    )

    illuminance = Observation.create(
        "illuminance",
        1500,
        unit="lux",
        location_id="living",
    )

    result = IlluminanceInterpreter().interpret(
        [illuminance]
    )

    assert result[0].value == "bright"


def test_illuminance_interpreter_ignores_missing_illuminance():
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
    )

    temperature = Observation.create(
        "temperature",
        25,
        unit="degC",
        location_id="living",
    )

    assert (
        IlluminanceInterpreter().interpret(
            [temperature]
        )
        == []
    )


def test_illuminance_interpreter_uses_location_knowledge():
    from src.smartscreen_platform.interpretation import (
        IlluminanceInterpreter,
    )

    knowledge = StaticKnowledge(
        global_values={
            "lighting_dim_below_lux": 80,
            "lighting_bright_above_lux": 1200,
        },
        location_values={
            "corridor": {
                "lighting_dim_below_lux": 50,
                "lighting_bright_above_lux": 500,
            }
        },
    )

    illuminance = Observation.create(
        "illuminance",
        60,
        unit="lux",
        location_id="corridor",
    )

    result = IlluminanceInterpreter().interpret(
        [illuminance],
        knowledge=knowledge,
    )

    assert result[0].value == "comfortable"

    assert result[0].metadata == {
        "dim_below_lux": 50.0,
        "bright_above_lux": 500.0,
    }

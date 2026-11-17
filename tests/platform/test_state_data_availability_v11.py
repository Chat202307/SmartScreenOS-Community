from src.smartscreen_platform.capabilities.comfort import (
    ComfortCapability,
)
from src.smartscreen_platform.capabilities.occupancy import (
    OccupancyCapability,
)
from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.interpretation import (
    PresenceInterpreter,
    ThermalInterpreter,
)


def test_missing_temperature_produces_no_thermal_state():
    observations = [
        Observation.create(
            "humidity",
            50,
            unit="percent",
            location_id="living",
        )
    ]

    interpretations = ThermalInterpreter().interpret(
        observations
    )

    assert interpretations == []


def test_temperature_without_humidity_can_produce_thermal_state():
    observations = [
        Observation.create(
            "temperature",
            25,
            unit="degC",
            location_id="living",
        )
    ]

    interpretations = ThermalInterpreter().interpret(
        observations
    )

    assert len(interpretations) == 1
    assert (
        interpretations[0].interpretation_type
        == "thermal_state"
    )


def test_temperature_without_humidity_produces_no_comfort():
    observations = [
        Observation.create(
            "temperature",
            25,
            unit="degC",
            location_id="living",
        )
    ]

    interpretations = ThermalInterpreter().interpret(
        observations
    )

    patches = ComfortCapability().evaluate(
        interpretations,
        observations=observations,
    )

    assert patches == []


def test_temperature_and_humidity_can_produce_comfort():
    observations = [
        Observation.create(
            "temperature",
            25,
            unit="degC",
            location_id="living",
        ),
        Observation.create(
            "humidity",
            50,
            unit="percent",
            location_id="living",
        ),
    ]

    interpretations = ThermalInterpreter().interpret(
        observations
    )

    patches = ComfortCapability().evaluate(
        interpretations,
        observations=observations,
    )

    assert len(patches) == 1
    assert patches[0].target == "comfort"
    assert patches[0].location_id == "living"


def test_missing_presence_produces_no_occupancy_interpretation():
    observations = [
        Observation.create(
            "temperature",
            25,
            unit="degC",
            location_id="living",
        )
    ]

    interpretations = PresenceInterpreter().interpret(
        observations
    )

    assert interpretations == []


def test_missing_presence_produces_no_occupancy_state():
    observations = [
        Observation.create(
            "temperature",
            25,
            unit="degC",
            location_id="living",
        )
    ]

    interpretations = PresenceInterpreter().interpret(
        observations
    )

    patches = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )

    assert patches == []


def test_explicit_false_presence_produces_unoccupied_state():
    observations = [
        Observation.create(
            "presence",
            False,
            location_id="living",
        )
    ]

    interpretations = PresenceInterpreter().interpret(
        observations
    )

    patches = OccupancyCapability().evaluate(
        interpretations,
        observations=observations,
    )

    assert len(patches) == 1

    assert patches[0].value == {
        "state": "unoccupied",
        "count": 0,
    }

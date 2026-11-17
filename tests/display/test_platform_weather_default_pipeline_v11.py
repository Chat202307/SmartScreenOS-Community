from pathlib import Path

from src.smartscreen_display.home_assistant_observations import (
    HomeAssistantObservationAdapter,
)
from src.smartscreen_display.platform_entities_config import (
    load_platform_entities,
)
from src.smartscreen_platform.capabilities.weather_advice import (
    WeatherAdviceCapability,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)
from src.smartscreen_platform.observation_accumulator import (
    ObservationAccumulator,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)


PROJECT = Path(__file__).resolve().parents[2]

PLATFORM_ENTITIES = (
    PROJECT
    / "config"
    / "platform_entities.json"
)


def make_pipeline():
    entities = load_platform_entities(
        PLATFORM_ENTITIES
    )

    adapter = HomeAssistantObservationAdapter(
        entities=entities,
    )

    freshness_by_location_parameter = {
        (
            entity["location_id"],
            entity["parameter"],
        ): entity["max_age_seconds"]
        for entity in entities
        if (
            "max_age_seconds" in entity
            and entity.get("location_id")
        )
    }

    accumulator = ObservationAccumulator(
        max_age_by_location_parameter=(
            freshness_by_location_parameter
        ),
    )

    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[],
        capabilities=[
            WeatherAdviceCapability(),
        ],
    )

    return (
        adapter,
        accumulator,
        pipeline,
        household_state,
    )


def push_state(
    adapter,
    accumulator,
    pipeline,
    state,
):
    observations = adapter.convert(
        state
    )

    observations = accumulator.update(
        observations
    )

    pipeline.process(
        observations,
        location_id="outdoor",
    )


def snapshot_by_target(household_state):
    return {
        item["target"]: item
        for item in household_state.snapshot()
    }







import json

from src.smartscreen_display.server import SnapshotApplication
from src.smartscreen_platform.capabilities.occupancy import (
    OccupancyCapability,
)
from src.smartscreen_platform.contracts import Observation
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
)
from src.smartscreen_platform.interpretation import (
    PresenceInterpreter,
)
from src.smartscreen_platform.state_pipeline import (
    PlatformStatePipeline,
)


class FakeHost:
    def snapshot(self):
        return {
            "schemaVersion": "1",
            "generatedAt": "2026-08-12T00:00:00+00:00",
            "runtime": {
                "installed": [],
                "sessions": [],
            },
            "scheduler": {
                "running": True,
                "backgroundRunning": True,
                "backgroundFailed": False,
                "lastBackgroundError": None,
                "intervalSeconds": 1.0,
                "nextRunAt": 100.0,
            },
            "capabilities": {},
        }


def test_presence_projects_to_dashboard_occupancy_card():
    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            PresenceInterpreter(),
        ],
        capabilities=[
            OccupancyCapability(),
        ],
    )

    presence = Observation.create(
        "presence",
        True,
        location_id="living",
    )

    entries = pipeline.process(
        [presence],
    )

    assert len(entries) == 1

    app = SnapshotApplication(
        FakeHost(),
        household_state_source=household_state,
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert headers["Content-Type"] == (
        "application/json; charset=utf-8"
    )

    assert len(payload["cards"]) == 1

    card = payload["cards"][0]

    assert card["kind"] == "state"
    assert card["target"] == "occupancy"
    assert card["value"] == {
        "state": "occupied",
        "count": None,
    }
    assert card["location_id"] == "living"
    assert card["metadata"] == {
        "model": "occupancy_v1",
    }


def test_explicit_absence_projects_to_dashboard_unoccupied_card():
    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            PresenceInterpreter(),
        ],
        capabilities=[
            OccupancyCapability(),
        ],
    )

    presence = Observation.create(
        "presence",
        False,
        location_id="living",
    )

    pipeline.process(
        [presence],
    )

    app = SnapshotApplication(
        FakeHost(),
        household_state_source=household_state,
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert len(payload["cards"]) == 1

    card = payload["cards"][0]

    assert card["target"] == "occupancy"
    assert card["value"] == {
        "state": "unoccupied",
        "count": 0,
    }

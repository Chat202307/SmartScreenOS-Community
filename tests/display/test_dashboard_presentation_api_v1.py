import json

from src.smartscreen_display.server import SnapshotApplication


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


class FakeHouseholdStateSource:
    def snapshot(self):
        return [
            {
                "target": "comfort",
                "value": {
                    "score": 72,
                    "level": "slightly_uncomfortable",
                },
                "confidence": 0.92,
                "updated_at": "2026-08-12T00:00:00+00:00",
                "ttl_seconds": 300,
                "location_id": "living-room",
                "source_capability": "comfort",
                "evidence_refs": [
                    "observation:temperature-1",
                    "observation:humidity-1",
                ],
                "metadata": {},
            }
        ]


def test_dashboard_api_builds_presentation_from_household_state():
    app = SnapshotApplication(
        FakeHost(),
        household_state_source=FakeHouseholdStateSource(),
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert headers["Content-Type"] == (
        "application/json; charset=utf-8"
    )

    assert payload == {
        "cards": [
            {
                "kind": "state",
                "target": "comfort",
                "value": {
                    "score": 72,
                    "level": "slightly_uncomfortable",
                },
                "confidence": 0.92,
                "location_id": "living-room",
                "evidence_refs": [
                    "observation:temperature-1",
                    "observation:humidity-1",
                ],
                "metadata": {},
                "updated_at": (
                    "2026-08-12T00:00:00+00:00"
                ),
            }
        ],
        "observations": [],
        "locations": [
            {
                "location_id": "living-room",
                "has_semantic_data": True,
                "semantic_targets": [
                    "comfort",
                ],
            }
        ],
    }


def test_dashboard_api_returns_empty_cards_without_household_state_source():
    app = SnapshotApplication(FakeHost())

    status, headers, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert payload == {
        "cards": [],
        "observations": [],
        "locations": [],
    }


def test_dashboard_api_is_read_only():
    app = SnapshotApplication(
        FakeHost(),
        household_state_source=FakeHouseholdStateSource(),
    )

    status, headers, body = app.handle(
        method="POST",
        path="/api/dashboard",
    )

    assert status == 405
    assert headers["Allow"] == "GET"


class FakeObservationSource:
    def snapshot(self):
        from src.smartscreen_platform.contracts import (
            Observation,
        )

        return [
            Observation.create(
                parameter="illuminance",
                value=45.0,
                unit="lux",
                location_id="corridor",
                provenance={
                    "provider":
                        "home_assistant",
                    "entity_id":
                        "sensor.corridor_illuminance",
                },
            ),
            Observation.create(
                parameter="motion_idle_seconds",
                value=120,
                unit="s",
                location_id="corridor",
                provenance={
                    "provider":
                        "home_assistant",
                    "entity_id":
                        "sensor.corridor_motion_idle",
                },
            ),
        ]


def test_dashboard_api_reads_generic_observation_source():
    from src.smartscreen_display.presentation import (
        DashboardPresentationBuilder,
    )

    app = SnapshotApplication(
        FakeHost(),
        observation_source=FakeObservationSource(),
        presentation_builder=(
            DashboardPresentationBuilder(
                location_labels={
                    "corridor": "过廊",
                },
                location_orders={
                    "corridor": 30,
                },
            )
        ),
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert len(
        payload["observations"]
    ) == 2

    illuminance = next(
        item
        for item in payload["observations"]
        if item["parameter"] == "illuminance"
    )

    assert illuminance["value"] == 45.0
    assert illuminance["unit"] == "lux"
    assert (
        illuminance["location_id"]
        == "corridor"
    )
    assert (
        illuminance["location_label"]
        == "过廊"
    )
    assert (
        illuminance["location_order"]
        == 30
    )

    motion = next(
        item
        for item in payload["observations"]
        if (
            item["parameter"]
            == "motion_idle_seconds"
        )
    )

    assert motion["value"] == 120
    assert motion["unit"] == "s"


def test_dashboard_api_without_observation_source_keeps_empty_observations():
    app = SnapshotApplication(
        FakeHost(),
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload["observations"] == []

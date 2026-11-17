from pathlib import Path

from src.smartscreen_display.presentation import (
    DashboardPresentationBuilder,
)


PROJECT = Path(__file__).resolve().parents[2]

DASHBOARD_JS = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "static"
    / "dashboard.js"
)


def dashboard_script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def test_presentation_exposes_lighting_as_room_semantic_target():
    builder = DashboardPresentationBuilder(
        location_labels={
            "corridor": "过廊",
        },
        location_orders={
            "corridor": 30,
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "lighting",
                "value": {
                    "state": "dim",
                },
                "confidence": 0.95,
                "location_id": "corridor",
                "evidence_refs": [
                    "observation:illuminance-1",
                ],
                "metadata": {
                    "model": "lighting_v1",
                },
            }
        ],
    )

    location = view.to_dict()["locations"][0]

    assert location["location_id"] == "corridor"
    assert location["has_semantic_data"] is True
    assert location["semantic_targets"] == [
        "lighting",
    ]


def test_presentation_orders_lighting_after_occupancy_and_comfort():
    builder = DashboardPresentationBuilder(
        location_labels={
            "corridor": "过廊",
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "lighting",
                "value": {
                    "state": "dim",
                },
                "confidence": 0.95,
                "location_id": "corridor",
                "evidence_refs": [],
                "metadata": {},
            },
            {
                "target": "comfort",
                "value": {
                    "level": "comfortable",
                    "score": 90,
                },
                "confidence": 0.9,
                "location_id": "corridor",
                "evidence_refs": [],
                "metadata": {},
            },
            {
                "target": "occupancy",
                "value": {
                    "state": "occupied",
                    "count": None,
                },
                "confidence": 0.9,
                "location_id": "corridor",
                "evidence_refs": [],
                "metadata": {},
            },
        ],
    )

    location = view.to_dict()["locations"][0]

    assert location["semantic_targets"] == [
        "occupancy",
        "comfort",
        "lighting",
    ]


def test_dashboard_routes_lighting_card_to_renderer():
    script = dashboard_script()

    assert (
        'cards[i].target === "lighting"'
        in script
    )

    assert (
        "renderLightingCard(cards[i])"
        in script
    )


def test_dashboard_lighting_renderer_handles_dim():
    script = dashboard_script()

    start = script.index(
        "function renderLightingCard"
    )

    section = script[
        start:start + 1500
    ]

    assert '"dim"' in section
    assert '"光线偏暗"' in section


def test_dashboard_lighting_renderer_handles_comfortable():
    script = dashboard_script()

    start = script.index(
        "function renderLightingCard"
    )

    section = script[
        start:start + 1500
    ]

    assert '"comfortable"' in section
    assert '"光线适宜"' in section


def test_dashboard_lighting_renderer_handles_bright():
    script = dashboard_script()

    start = script.index(
        "function renderLightingCard"
    )

    section = script[
        start:start + 1500
    ]

    assert '"bright"' in section
    assert '"光线较亮"' in section


def test_dashboard_lighting_renderer_uses_location_label():
    script = dashboard_script()

    start = script.index(
        "function renderLightingCard"
    )

    section = script[
        start:start + 1500
    ]

    assert "card.location_id" in section
    assert "card.location_label" in section
    assert "locationLabel || locationId" in section


def test_dashboard_lighting_has_location_specific_semantic_node():
    script = dashboard_script()

    start = script.index(
        "function renderLightingCard"
    )

    section = script[
        start:start + 1500
    ]

    assert (
        '"semantic-lighting-status"'
        in section
    )

    assert (
        "semanticStatusNodeId("
        in section
    )


def test_semantic_priority_places_lighting_after_comfort():
    script = dashboard_script()

    start = script.index(
        "function semanticTargetPriority"
    )

    end = script.index(
        "function sortSemanticCards",
        start,
    )

    section = script[start:end]

    occupancy = section.index(
        '"occupancy"'
    )

    comfort = section.index(
        '"comfort"'
    )

    lighting = section.index(
        '"lighting"'
    )

    assert occupancy < comfort < lighting

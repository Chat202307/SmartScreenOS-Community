from src.smartscreen_display.presentation import (
    DashboardPresentationBuilder,
)


def test_weather_advice_is_projected_as_dashboard_card():
    builder = DashboardPresentationBuilder(
        location_labels={
            "outdoor": "室外",
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "umbrella_advice",
                "value": {
                    "recommended": True,
                    "reason": "rain_forecast",
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [
                    "obs-rain",
                ],
                "metadata": {
                    "model": "weather_advice_v1",
                },
            }
        ],
    )

    payload = view.to_dict()

    assert payload["cards"] == [
        {
            "kind": "state",
            "target": "umbrella_advice",
            "value": {
                "recommended": True,
                "reason": "rain_forecast",
            },
            "confidence": 0.9,
            "location_id": "outdoor",
            "location_label": "室外",
            "evidence_refs": [
                "obs-rain",
            ],
            "metadata": {
                "model": "weather_advice_v1",
            },
        }
    ]


def test_clothing_advice_is_projected_as_dashboard_card():
    builder = DashboardPresentationBuilder()

    view = builder.build(
        household_states=[
            {
                "target": "clothing_advice",
                "value": {
                    "level": "warm",
                    "reason": (
                        "cold_apparent_temperature"
                    ),
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    card = view.to_dict()["cards"][0]

    assert card["target"] == (
        "clothing_advice"
    )
    assert card["value"]["level"] == "warm"


def test_weather_advice_does_not_count_as_room_semantic_target():
    builder = DashboardPresentationBuilder(
        location_labels={
            "outdoor": "室外",
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "umbrella_advice",
                "value": {
                    "recommended": True,
                    "reason": "rain_forecast",
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [],
                "metadata": {},
            },
            {
                "target": "clothing_advice",
                "value": {
                    "level": "warm",
                    "reason": (
                        "cold_apparent_temperature"
                    ),
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [],
                "metadata": {},
            },
        ],
    )

    location = view.to_dict()["locations"][0]

    assert location["location_id"] == "outdoor"
    assert location["has_semantic_data"] is False
    assert location["semantic_targets"] == []


def test_weather_advice_does_not_mask_missing_room_semantics():
    builder = DashboardPresentationBuilder(
        location_labels={
            "outdoor": "室外",
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "umbrella_advice",
                "value": {
                    "recommended": True,
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [],
                "metadata": {},
            },
            {
                "target": "occupancy",
                "value": {
                    "state": "occupied",
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [],
                "metadata": {},
            },
        ],
    )

    location = view.to_dict()["locations"][0]

    assert location["has_semantic_data"] is True
    assert location["semantic_targets"] == [
        "occupancy",
    ]


def test_weather_advice_location_is_still_preserved():
    builder = DashboardPresentationBuilder()

    view = builder.build(
        household_states=[
            {
                "target": "umbrella_advice",
                "value": {
                    "recommended": False,
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    locations = view.to_dict()["locations"]

    assert len(locations) == 1
    assert (
        locations[0]["location_id"]
        == "outdoor"
    )


def test_dashboard_card_preserves_household_state_updated_at():
    from src.smartscreen_display.presentation.builder import (
        DashboardPresentationBuilder,
    )

    updated_at = "2026-08-13T14:22:00+00:00"

    view = DashboardPresentationBuilder().build(
        household_states=[
            {
                "target": "weather_status",
                "value": {
                    "condition": "partlycloudy",
                    "temperature": 24.4,
                },
                "confidence": 0.9,
                "location_id": "outdoor",
                "updated_at": updated_at,
                "evidence_refs": [],
                "metadata": {
                    "model": "weather_status_v1",
                },
            }
        ]
    )

    payload = view.to_dict()

    assert payload["cards"][0]["updated_at"] == updated_at

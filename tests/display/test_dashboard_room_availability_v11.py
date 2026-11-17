from src.smartscreen_display.presentation import (
    DashboardPresentationBuilder,
)


def test_presentation_exposes_known_room_without_semantic_state():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "家庭活动室",
            "study": "阅读室",
        },
        location_orders={
            "living": 10,
            "study": 20,
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "occupancy",
                "value": {
                    "state": "occupied",
                    "count": None,
                },
                "confidence": 0.9,
                "location_id": "living",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    payload = view.to_dict()

    assert "locations" in payload

    assert payload["locations"] == [
        {
            "location_id": "living",
            "location_label": "家庭活动室",
            "location_order": 10,
            "has_semantic_data": True,
            "semantic_targets": [
                "occupancy",
            ],
        },
        {
            "location_id": "study",
            "location_label": "阅读室",
            "location_order": 20,
            "has_semantic_data": False,
            "semantic_targets": [],
        },
    ]


def test_location_availability_uses_stable_id_not_label():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "用户随便改的名字",
        },
        location_orders={
            "living": 10,
        },
    )

    view = builder.build(
        household_states=[],
    )

    location = view.to_dict()["locations"][0]

    assert location["location_id"] == "living"
    assert (
        location["location_label"]
        == "用户随便改的名字"
    )
    assert location["has_semantic_data"] is False


def test_unknown_semantic_location_is_still_preserved():
    builder = DashboardPresentationBuilder()

    view = builder.build(
        household_states=[
            {
                "target": "occupancy",
                "value": {
                    "state": "occupied",
                    "count": None,
                },
                "confidence": 0.9,
                "location_id": "temporary-room",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    locations = view.to_dict()["locations"]

    assert locations == [
        {
            "location_id": "temporary-room",
            "has_semantic_data": True,
            "semantic_targets": [
                "occupancy",
            ],
        }
    ]


def test_locationless_semantic_state_does_not_create_room():
    builder = DashboardPresentationBuilder()

    view = builder.build(
        household_states=[
            {
                "target": "comfort",
                "value": {
                    "level": "comfortable",
                    "score": 90,
                },
                "confidence": 0.9,
                "location_id": None,
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    assert view.to_dict()["locations"] == []

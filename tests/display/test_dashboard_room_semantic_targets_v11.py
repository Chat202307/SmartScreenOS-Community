from src.smartscreen_display.presentation import (
    DashboardPresentationBuilder,
)


def test_location_exposes_available_semantic_targets():
    builder = DashboardPresentationBuilder(
        location_labels={
            "study": "阅读室",
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
                "location_id": "study",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    location = view.to_dict()["locations"][0]

    assert location["location_id"] == "study"
    assert location["has_semantic_data"] is True
    assert location["semantic_targets"] == [
        "occupancy",
    ]


def test_location_exposes_multiple_semantic_targets():
    builder = DashboardPresentationBuilder(
        location_labels={
            "study": "阅读室",
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "comfort",
                "value": {
                    "level": "comfortable",
                    "score": 90,
                },
                "confidence": 0.9,
                "location_id": "study",
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
                "location_id": "study",
                "evidence_refs": [],
                "metadata": {},
            },
        ],
    )

    location = view.to_dict()["locations"][0]

    assert location["semantic_targets"] == [
        "occupancy",
        "comfort",
    ]


def test_known_room_without_semantic_data_has_no_targets():
    builder = DashboardPresentationBuilder(
        location_labels={
            "study": "阅读室",
        },
    )

    view = builder.build(
        household_states=[],
    )

    location = view.to_dict()["locations"][0]

    assert location["has_semantic_data"] is False
    assert location["semantic_targets"] == []


def test_semantic_targets_are_location_specific():
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
            },
            {
                "target": "comfort",
                "value": {
                    "level": "comfortable",
                    "score": 90,
                },
                "confidence": 0.9,
                "location_id": "study",
                "evidence_refs": [],
                "metadata": {},
            },
        ],
    )

    locations = {
        item["location_id"]: item
        for item in view.to_dict()["locations"]
    }

    assert locations["living"]["semantic_targets"] == [
        "occupancy",
    ]
    assert locations["study"]["semantic_targets"] == [
        "comfort",
    ]


def test_locationless_semantic_state_is_not_room_target():
    builder = DashboardPresentationBuilder(
        location_labels={
            "study": "阅读室",
        },
    )

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

    location = view.to_dict()["locations"][0]

    assert location["semantic_targets"] == []

import json

from src.smartscreen_display.presentation import (
    DashboardPresentationBuilder,
)


def test_presentation_uses_room_label_for_location():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "一楼家庭活动区",
            "study": "我的工作间",
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

    card = view.cards[0]

    assert card.location_id == "living"
    assert card.location_label == "一楼家庭活动区"


def test_presentation_preserves_unknown_location_id():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "一楼家庭活动区",
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
                "location_id": "garage",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    card = view.cards[0]

    assert card.location_id == "garage"
    assert card.location_label is None


def test_location_label_is_serialized():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "一楼家庭活动区",
        },
    )

    payload = builder.build(
        household_states=[
            {
                "target": "comfort",
                "value": {
                    "level": "comfortable",
                    "score": 92,
                },
                "confidence": 0.9,
                "location_id": "living",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    ).to_dict()

    assert payload["cards"][0]["location_id"] == "living"
    assert payload["cards"][0]["location_label"] == "一楼家庭活动区"


def test_location_label_is_optional_without_location_id():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "一楼家庭活动区",
        },
    )

    view = builder.build(
        household_states=[
            {
                "target": "comfort",
                "value": {
                    "level": "comfortable",
                    "score": 92,
                },
                "confidence": 0.9,
                "location_id": None,
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    assert view.cards[0].location_label is None


class FakeHouseholdStateSource:
    def snapshot(self):
        return [
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
        ]


class FakeHost:
    def snapshot(self):
        return {
            "schemaVersion": "1.0",
            "capabilities": {},
        }


def test_snapshot_application_accepts_presentation_builder():
    import json

    from src.smartscreen_display.server import (
        SnapshotApplication,
    )

    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "用户自己的房间名称",
        },
    )

    app = SnapshotApplication(
        FakeHost(),
        household_state_source=(
            FakeHouseholdStateSource()
        ),
        presentation_builder=builder,
    )

    status, _, body = app.handle(
        method="GET",
        path="/api/dashboard",
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert (
        payload["cards"][0]["location_label"]
        == "用户自己的房间名称"
    )


def test_presentation_adds_location_order():
    builder = DashboardPresentationBuilder(
        location_labels={
            "living": "家庭活动室",
        },
        location_orders={
            "living": 20,
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
                "location_id": "living",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    assert view.cards[0].location_order == 20

    payload = view.to_dict()

    assert (
        payload["cards"][0]["location_order"]
        == 20
    )


def test_location_order_is_optional():
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
                "location_id": "unknown-room",
                "evidence_refs": [],
                "metadata": {},
            }
        ],
    )

    assert view.cards[0].location_order is None


def test_home_config_preserves_chinese_outdoor_label(tmp_path):

    from src.smartscreen_display.location_labels_config import (
        load_location_labels,
    )

    home_file = tmp_path / "home.json"
    home_file.write_text(
        json.dumps({"rooms": [{"id": "outdoor", "name": "室外"}]}),
        encoding="utf-8",
    )
    labels = load_location_labels(home_file)

    assert labels["outdoor"] == "室外"

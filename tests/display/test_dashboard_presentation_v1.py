from src.smartscreen_display.presentation import (
    DashboardPresentationBuilder,
)


def test_dashboard_presentation_builds_state_card():
    builder = DashboardPresentationBuilder()

    state = {
        "target": "home.temperature",
        "value": 24.5,
        "confidence": 0.92,
        "updated_at": "2026-08-12T00:00:00+00:00",
        "ttl_seconds": 300,
        "location_id": "living-room",
        "source_capability": "comfort",
        "evidence_refs": ["observation:temperature-1"],
        "metadata": {},
    }

    view = builder.build(
        household_states=[state],
    )

    assert len(view.cards) == 1

    card = view.cards[0]

    assert card.kind == "state"
    assert card.target == "home.temperature"
    assert card.value == 24.5
    assert card.confidence == 0.92
    assert card.location_id == "living-room"
    assert card.evidence_refs == (
        "observation:temperature-1",
    )


def test_dashboard_presentation_serializes_view_model():
    builder = DashboardPresentationBuilder()

    view = builder.build(
        household_states=[
            {
                "target": "home.presence",
                "value": "occupied",
                "confidence": 0.88,
                "updated_at": "2026-08-12T00:00:00+00:00",
                "ttl_seconds": 120,
                "location_id": "living-room",
                "source_capability": "presence",
                "evidence_refs": ["observation:presence-1"],
                "metadata": {},
            }
        ],
    )

    payload = view.to_dict()

    assert payload["cards"][0]["kind"] == "state"
    assert payload["cards"][0]["target"] == "home.presence"
    assert payload["cards"][0]["evidence_refs"] == [
        "observation:presence-1"
    ]


def test_dashboard_presentation_builds_observation_item():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    builder = DashboardPresentationBuilder(
        location_labels={
            "corridor": "过廊",
        },
        location_orders={
            "corridor": 30,
        },
    )

    observation = Observation.create(
        parameter="illuminance",
        value=45.0,
        unit="lux",
        location_id="corridor",
        provenance={
            "provider": "home_assistant",
            "entity_id":
                "sensor.corridor_illuminance",
        },
    )

    view = builder.build(
        household_states=[],
        observations=[
            observation,
        ],
    )

    assert len(view.observations) == 1

    item = view.observations[0]

    assert item.parameter == "illuminance"
    assert item.value == 45.0
    assert item.unit == "lux"
    assert item.location_id == "corridor"
    assert item.location_label == "过廊"
    assert item.location_order == 30
    assert item.observation_id == (
        observation.observation_id
    )
    assert item.observed_at == (
        observation.observed_at
    )


def test_dashboard_presentation_serializes_observations():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    builder = DashboardPresentationBuilder(
        location_labels={
            "corridor": "过廊",
        },
        location_orders={
            "corridor": 30,
        },
    )

    motion = Observation.create(
        parameter="motion_idle_seconds",
        value=120,
        unit="s",
        location_id="corridor",
        provenance={
            "provider": "home_assistant",
            "entity_id":
                "sensor.corridor_motion_idle",
        },
    )

    view = builder.build(
        household_states=[],
        observations=[
            motion,
        ],
    )

    payload = view.to_dict()

    assert payload["observations"] == [
        {
            "observation_id":
                motion.observation_id,
            "parameter":
                "motion_idle_seconds",
            "value": 120,
            "unit": "s",
            "confidence": 1.0,
            "quality": "good",
            "location_id": "corridor",
            "location_label": "过廊",
            "location_order": 30,
            "observed_at":
                motion.observed_at,
            "provenance": {
                "provider":
                    "home_assistant",
                "entity_id":
                    "sensor.corridor_motion_idle",
            },
            "metadata": {},
        }
    ]


def test_observation_location_is_in_dashboard_locations():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    builder = DashboardPresentationBuilder(
        location_labels={
            "corridor": "过廊",
        },
        location_orders={
            "corridor": 30,
        },
    )

    observation = Observation.create(
        parameter="illuminance",
        value=45,
        unit="lux",
        location_id="corridor",
    )

    view = builder.build(
        household_states=[],
        observations=[
            observation,
        ],
    )

    assert (
        view.to_dict()["locations"]
        == [
            {
                "location_id": "corridor",
                "has_semantic_data": False,
                "semantic_targets": [],
                "location_label": "过廊",
                "location_order": 30,
            }
        ]
    )


def test_presentation_projects_location_zones():
    from src.smartscreen_display.presentation.builder import (
        DashboardPresentationBuilder,
    )

    builder = DashboardPresentationBuilder(
        location_labels={
            "open_public_area": "客餐厨开放区",
        },
        location_orders={
            "open_public_area": 15,
        },
        location_zones={
            "open_public_area": (
                "living",
                "dining",
                "kitchen",
            ),
        },
    )

    payload = builder.build(
        household_states=[],
        observations=[],
    ).to_dict()

    assert payload["zones"] == [
        {
            "zone_id": "open_public_area",
            "location_label": "客餐厨开放区",
            "location_order": 15,
            "room_ids": [
                "living",
                "dining",
                "kitchen",
            ],
        }
    ]


def test_presentation_omits_zones_when_unconfigured():
    from src.smartscreen_display.presentation.builder import (
        DashboardPresentationBuilder,
    )

    payload = DashboardPresentationBuilder().build(
        household_states=[],
        observations=[],
    ).to_dict()

    assert "zones" not in payload



def test_presentation_zone_can_project_summary_location():
    from src.smartscreen_display.presentation.model import (
        DashboardZone,
    )

    zone = DashboardZone(
        zone_id="home_living_dining",
        room_ids=(
            "living",
            "dining",
        ),
        summary_location_id=(
            "open_public_area"
        ),
        location_label="客餐厅",
        location_order=20,
    )

    assert zone.to_dict() == {
        "zone_id": "home_living_dining",
        "room_ids": [
            "living",
            "dining",
        ],
        "summary_location_id":
            "open_public_area",
        "location_label": "客餐厅",
        "location_order": 20,
    }



def test_presentation_builder_projects_summary_location_from_zone_config():
    from src.smartscreen_display.presentation.builder import (
        DashboardPresentationBuilder,
    )

    builder = DashboardPresentationBuilder(
        location_labels={
            "home_living_dining": "客餐厅",
        },
        location_orders={
            "home_living_dining": 20,
        },
        location_zones={
            "home_living_dining": {
                "room_ids": (
                    "living",
                    "dining",
                ),
                "summary_location_id":
                    "open_public_area",
                "show_on_home": True,
            },
        },
    )

    payload = builder.build(
        household_states=[],
        observations=[],
    ).to_dict()

    assert payload["zones"] == [
        {
            "zone_id": "home_living_dining",
            "room_ids": [
                "living",
                "dining",
            ],
            "summary_location_id":
                "open_public_area",
            "location_label": "客餐厅",
            "show_on_home": True,
            "location_order": 20,
        }
    ]



def test_presentation_zone_can_be_marked_for_home():
    from src.smartscreen_display.presentation.model import (
        DashboardZone,
    )

    zone = DashboardZone(
        zone_id="home_kitchen",
        room_ids=("kitchen",),
        summary_location_id="open_public_area",
        location_label="厨房",
        location_order=10,
        show_on_home=True,
    )

    assert zone.to_dict() == {
        "zone_id": "home_kitchen",
        "room_ids": ["kitchen"],
        "summary_location_id":
            "open_public_area",
        "location_label": "厨房",
        "location_order": 10,
        "show_on_home": True,
    }


def test_presentation_zone_projects_sheet_layout_metadata():
    from src.smartscreen_display.presentation.builder import (
        DashboardPresentationBuilder,
    )

    builder = DashboardPresentationBuilder(
        location_zones={
            "home_living_dining": {
                "room_ids": (
                    "living",
                    "dining",
                ),
                "sheet_extra_device_ids": (
                    "device.shared",
                ),
                "sheet_device_order": (
                    "device.a",
                    "device.b",
                ),
                "sheet_wide_device_ids": (
                    "device.b",
                ),
            },
        },
    )

    payload = builder.build(
        household_states=[],
        observations=[],
    ).to_dict()

    zone = payload["zones"][0]

    assert zone["room_ids"] == [
        "living",
        "dining",
    ]

    assert zone["sheet_extra_device_ids"] == [
        "device.shared",
    ]

    assert zone["sheet_device_order"] == [
        "device.a",
        "device.b",
    ]

    assert zone["sheet_wide_device_ids"] == [
        "device.b",
    ]

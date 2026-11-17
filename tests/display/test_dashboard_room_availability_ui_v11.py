from pathlib import Path


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


def room_availability_section():
    script = dashboard_script()

    start = script.index(
        "function renderRoomAvailability"
    )

    end = script.index(
        "function renderOccupancyCard",
        start,
    )

    return script[start:end]


def test_room_availability_hook_exists():
    section = room_availability_section()

    assert "function renderRoomAvailability" in section


def test_room_without_semantic_data_is_not_rendered_as_placeholder():
    section = room_availability_section()

    assert "暂无环境数据" not in section
    assert "semantic-room-empty" not in section


def test_room_availability_does_not_create_location_specific_empty_node():
    section = room_availability_section()

    assert "semanticStatusNodeId(" not in section
    assert "semantic-room-empty" not in section


def test_room_with_semantic_data_relies_on_real_semantic_cards():
    section = room_availability_section()

    assert "has_semantic_data" not in section
    assert "semantic_targets" not in section
    assert "return;" in section

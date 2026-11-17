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


def partial_renderer_section():
    script = dashboard_script()

    start = script.index(
        "function renderRoomAvailability"
    )

    end = script.index(
        "function renderOccupancyCard",
        start,
    )

    return script[start:end]


def test_room_availability_remains_a_defined_hook():
    section = partial_renderer_section()

    assert "function renderRoomAvailability" in section


def test_room_availability_does_not_render_empty_room_placeholder():
    section = partial_renderer_section()

    assert '"暂无环境数据"' not in section
    assert '"semantic-room-empty"' not in section


def test_room_availability_does_not_render_missing_target_placeholders():
    section = partial_renderer_section()

    assert '"舒适度 · 暂无数据"' not in section
    assert '"人员状态 · 暂无数据"' not in section
    assert '"semantic-comfort-missing"' not in section
    assert '"semantic-occupancy-missing"' not in section


def test_room_availability_keeps_api_availability_separate_from_ui():
    section = partial_renderer_section()

    assert "only renders semantic states" in section

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


def semantic_update_section():
    script = dashboard_script()

    start = script.index(
        "function updateSemanticDashboard"
    )
    end = script.index(
        "function scheduleSemanticDashboardRefresh",
        start,
    )

    return script[start:end]


def stale_cleanup_section():
    script = dashboard_script()

    start = script.index(
        "function removeStaleSemanticStatusItems"
    )
    end = script.index(
        "function semanticTargetPriority",
        start,
    )

    return script[start:end]


def test_room_availability_hook_remains_defined():
    section = room_availability_section()

    assert "function renderRoomAvailability" in section


def test_room_availability_does_not_create_empty_room_nodes():
    section = room_availability_section()

    assert "semantic-room-empty" not in section
    assert "暂无环境数据" not in section


def test_room_availability_does_not_create_missing_target_nodes():
    section = room_availability_section()

    assert "semantic-comfort-missing" not in section
    assert "semantic-occupancy-missing" not in section
    assert "renderMissingTarget" not in section


def test_room_availability_does_not_mark_placeholder_nodes_seen():
    section = room_availability_section()

    assert "seenSemanticNodeIds[" not in section


def test_semantic_refresh_runs_stale_cleanup_after_room_availability():
    section = semantic_update_section()

    render_index = section.index(
        "renderRoomAvailability("
    )

    cleanup_index = section.index(
        "removeStaleSemanticStatusItems("
    )

    assert render_index < cleanup_index


def test_stale_cleanup_removes_nodes_absent_from_seen_set():
    section = stale_cleanup_section()

    assert (
        "if (!seenSemanticNodeIds[item.id])"
        in section
    )

    assert (
        "container.removeChild(item)"
        in section
    )


def test_real_semantic_nodes_still_use_cleanup_class():
    script = dashboard_script()

    assert (
        'item.className = "semantic-status-item"'
        in script
    )


def test_real_semantic_nodes_are_marked_seen_during_dispatch():
    section = semantic_update_section()

    assert (
        "seenSemanticNodeIds[\n"
        "            occupancyNodeId"
        in section
    )

    assert (
        "seenSemanticNodeIds[\n"
        "            comfortNodeId"
        in section
    )

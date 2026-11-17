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


def test_semantic_node_identity_uses_location_id():
    script = dashboard_script()

    assert "semanticStatusNodeId" in script
    assert "locationId" in script
    assert "encodeURIComponent(locationId)" in script


def test_locationless_semantic_card_keeps_legacy_node_id():
    script = dashboard_script()

    start = script.index(
        "function semanticStatusNodeId"
    )
    section = script[start:start + 700]

    assert "if (!locationId)" in section
    assert "return baseId;" in section


def test_occupancy_renderer_uses_location_specific_node_id():
    script = dashboard_script()

    start = script.index(
        "function renderOccupancyCard"
    )
    section = script[start:start + 1300]

    assert "semanticStatusNodeId(" in section
    assert '"semantic-occupancy-status"' in section
    assert "locationId" in section


def test_comfort_renderer_uses_location_specific_node_id():
    script = dashboard_script()

    start = script.index(
        "function renderComfortCard"
    )
    section = script[start:start + 1600]

    assert "semanticStatusNodeId(" in section
    assert '"semantic-comfort-status"' in section
    assert "locationId" in section


def test_semantic_refresh_tracks_rendered_node_ids():
    script = dashboard_script()

    assert "seenSemanticNodeIds" in script


def test_occupancy_node_is_marked_seen_after_dispatch():
    script = dashboard_script()

    start = script.index(
        'cards[i].target === "occupancy"'
    )
    section = script[start:start + 700]

    assert "semanticStatusNodeId(" in section
    assert "seenSemanticNodeIds" in section


def test_comfort_node_is_marked_seen_after_dispatch():
    script = dashboard_script()

    start = script.index(
        'cards[i].target === "comfort"'
    )
    section = script[start:start + 700]

    assert "semanticStatusNodeId(" in section
    assert "seenSemanticNodeIds" in section


def test_stale_cleanup_operates_per_semantic_node():
    script = dashboard_script()

    assert "removeStaleSemanticStatusItems" in script
    assert "seenSemanticNodeIds" in script


def test_stale_cleanup_runs_after_card_dispatch():
    script = dashboard_script()

    dispatch = script.index(
        "for (var i = 0; i < cards.length; i += 1)"
    )
    cleanup = script.index(
        "removeStaleSemanticStatusItems"
    )

    # Ignore the function declaration; find its invocation
    # occurring after card dispatch.
    cleanup_call = script.index(
        "removeStaleSemanticStatusItems(",
        dispatch,
    )

    assert cleanup_call > dispatch


def test_semantic_identity_does_not_use_location_label():
    script = dashboard_script()

    start = script.index(
        "function semanticStatusNodeId"
    )
    section = script[start:start + 700]

    assert "location_label" not in section
    assert "locationLabel" not in section

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


def test_semantic_dashboard_tracks_seen_nodes():
    script = dashboard_script()

    assert "seenSemanticNodeIds" in script


def test_semantic_dashboard_tracks_occupancy_node():
    script = dashboard_script()

    start = script.index(
        'cards[i].target === "occupancy"'
    )
    section = script[start:start + 700]

    assert '"semantic-occupancy-status"' in section
    assert "seenSemanticNodeIds" in section


def test_semantic_dashboard_tracks_comfort_node():
    script = dashboard_script()

    start = script.index(
        'cards[i].target === "comfort"'
    )
    section = script[start:start + 700]

    assert '"semantic-comfort-status"' in section
    assert "seenSemanticNodeIds" in section


def test_semantic_dashboard_removes_missing_nodes():
    script = dashboard_script()

    assert "removeStaleSemanticStatusItems" in script
    assert ".removeChild(" in script


def test_semantic_dashboard_clears_stale_cards_after_dispatch():
    script = dashboard_script()

    dispatch = script.index(
        "for (var i = 0; i < cards.length; i += 1)"
    )

    cleanup = script.index(
        "removeStaleSemanticStatusItems(",
        dispatch,
    )

    assert cleanup > dispatch

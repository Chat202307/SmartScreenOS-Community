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


def test_semantic_dashboard_has_card_sorter():
    script = dashboard_script()

    assert "sortSemanticCards" in script


def test_semantic_sort_uses_location_identity():
    script = dashboard_script()

    start = script.index(
        "function sortSemanticCards"
    )
    section = script[start:start + 1800]

    assert "location_id" in section


def test_semantic_sort_has_stable_target_priority():
    script = dashboard_script()

    assert "semanticTargetPriority" in script

    start = script.index(
        "function semanticTargetPriority"
    )
    section = script[start:start + 700]

    assert '"occupancy"' in section
    assert '"comfort"' in section


def test_occupancy_precedes_comfort_within_location():
    script = dashboard_script()

    start = script.index(
        "function semanticTargetPriority"
    )
    section = script[start:start + 700]

    occupancy = section.index(
        '"occupancy"'
    )
    comfort = section.index(
        '"comfort"'
    )

    assert occupancy < comfort


def test_semantic_cards_are_sorted_before_dispatch():
    script = dashboard_script()

    sort_call = script.index(
        "sortSemanticCards("
    )

    dispatch = script.index(
        "for (var i = 0; i < cards.length; i += 1)"
    )

    assert sort_call < dispatch


def test_semantic_sort_does_not_use_location_label_for_identity():
    script = dashboard_script()

    start = script.index(
        "function sortSemanticCards"
    )
    section = script[start:start + 1800]

    assert "location_id" in section
    assert "location_label" not in section


def test_semantic_sort_prefers_location_order():
    script = dashboard_script()

    start = script.index(
        "function sortSemanticCards"
    )
    section = script[start:start + 2200]

    assert "location_order" in section


def test_location_id_remains_ordering_fallback():
    script = dashboard_script()

    start = script.index(
        "function sortSemanticCards"
    )
    section = script[start:start + 2200]

    assert "location_id" in section

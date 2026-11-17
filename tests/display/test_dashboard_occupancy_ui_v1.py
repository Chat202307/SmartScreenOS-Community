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


def test_dashboard_fetches_semantic_dashboard_api():
    script = dashboard_script()

    assert "/api/dashboard" in script


def test_dashboard_handles_occupancy_cards():
    script = dashboard_script()

    assert '"occupancy"' in script


def test_dashboard_handles_occupied_state():
    script = dashboard_script()

    assert '"occupied"' in script


def test_dashboard_handles_unoccupied_state():
    script = dashboard_script()

    assert '"unoccupied"' in script


def test_dashboard_routes_occupancy_card_to_renderer():
    script = dashboard_script()

    assert (
        'cards[i].target === "occupancy"'
        in script
    )
    assert "renderOccupancyCard(cards[i])" in script


def test_dashboard_renders_occupancy_into_semantic_status_container():
    script = dashboard_script()

    assert '"semantic-status-list"' in script
    assert '"当前有人"' in script
    assert '"当前无人"' in script

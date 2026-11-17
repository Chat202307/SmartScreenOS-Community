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


def test_dashboard_handles_comfort_cards():
    script = dashboard_script()

    assert '"comfort"' in script


def test_dashboard_routes_comfort_card_to_renderer():
    script = dashboard_script()

    assert (
        'cards[i].target === "comfort"'
        in script
    )
    assert "renderComfortCard(cards[i])" in script


def test_dashboard_handles_comfortable_level():
    script = dashboard_script()

    assert '"comfortable"' in script
    assert '"舒适"' in script


def test_dashboard_handles_slightly_uncomfortable_level():
    script = dashboard_script()

    assert '"slightly_uncomfortable"' in script
    assert '"稍有不适"' in script


def test_dashboard_handles_uncomfortable_level():
    script = dashboard_script()

    assert '"uncomfortable"' in script
    assert '"不舒适"' in script


def test_dashboard_renders_comfort_score():
    script = dashboard_script()

    assert "card.value.score" in script
    assert "舒适度 " in script


def test_semantic_occupancy_and_comfort_use_separate_nodes():
    script = dashboard_script()

    assert '"semantic-occupancy-status"' in script
    assert '"semantic-comfort-status"' in script
    assert "container.appendChild(item)" in script


def test_occupancy_renderer_does_not_replace_semantic_container():
    script = dashboard_script()

    start = script.index(
        "function renderOccupancyCard"
    )
    end = script.index(
        "function renderComfortCard"
    )

    occupancy_renderer = script[start:end]

    assert "container.innerHTML" not in occupancy_renderer

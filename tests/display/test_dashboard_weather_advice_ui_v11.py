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


def test_dashboard_has_umbrella_advice_renderer():
    script = dashboard_script()

    assert "renderUmbrellaAdviceCard" in script


def test_dashboard_has_clothing_advice_renderer():
    script = dashboard_script()

    assert "renderClothingAdviceCard" in script


def test_umbrella_advice_has_stable_node_id():
    script = dashboard_script()

    start = script.index(
        "function renderUmbrellaAdviceCard"
    )
    section = script[start:start + 1800]

    assert (
        '"semantic-umbrella-advice"'
        in section
    )
    assert "semanticStatusNodeId(" in section


def test_umbrella_advice_recommends_carrying_umbrella():
    script = dashboard_script()

    start = script.index(
        "function renderUmbrellaAdviceCard"
    )
    section = script[start:start + 1800]

    assert "recommended" in section
    assert '"建议带伞"' in section
    assert '"无需带伞"' in section


def test_clothing_advice_has_stable_node_id():
    script = dashboard_script()

    start = script.index(
        "function renderClothingAdviceCard"
    )
    section = script[start:start + 2200]

    assert (
        '"semantic-clothing-advice"'
        in section
    )
    assert "semanticStatusNodeId(" in section


def test_clothing_advice_maps_known_levels():
    script = dashboard_script()

    start = script.index(
        "function renderClothingAdviceCard"
    )
    section = script[start:start + 2200]

    assert '"warm"' in section
    assert '"light"' in section
    assert '"hot_weather"' in section

    assert '"注意保暖"' in section
    assert '"轻便着装"' in section
    assert '"清凉着装"' in section


def test_weather_advice_prefers_location_label():
    script = dashboard_script()

    start = script.index(
        "function renderUmbrellaAdviceCard"
    )
    end = script.index(
        "function updateSemanticDashboard",
        start,
    )
    section = script[start:end]

    assert "location_label" in section
    assert "location_id" in section


def test_weather_advice_is_dispatched_from_semantic_update():
    script = dashboard_script()

    assert (
        'cards[i].target === "umbrella_advice"'
        in script
    )
    assert (
        'cards[i].target === "clothing_advice"'
        in script
    )

    assert "renderUmbrellaAdviceCard(" in script
    assert "renderClothingAdviceCard(" in script


def test_weather_advice_nodes_participate_in_stale_cleanup():
    script = dashboard_script()

    assert (
        '"semantic-umbrella-advice"'
        in script
    )
    assert (
        '"semantic-clothing-advice"'
        in script
    )
    assert "seenSemanticNodeIds" in script


def test_weather_advice_has_stable_sort_priority():
    script = dashboard_script()

    start = script.index(
        "function semanticTargetPriority"
    )
    end = script.index(
        "function sortSemanticCards",
        start,
    )
    section = script[start:end]

    assert '"umbrella_advice"' in section
    assert '"clothing_advice"' in section

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


def test_umbrella_node_is_seen_only_when_card_exists():
    script = dashboard_script()

    target = (
        'cards[i].target === '
        '"umbrella_advice"'
    )

    start = script.index(target)
    section = script[start:start + 1200]

    assert (
        '"semantic-umbrella-advice"'
        in section
    )
    assert (
        "seenSemanticNodeIds["
        in section
    )
    assert (
        "renderUmbrellaAdviceCard("
        in section
    )


def test_clothing_node_is_seen_only_when_card_exists():
    script = dashboard_script()

    target = (
        'cards[i].target === '
        '"clothing_advice"'
    )

    start = script.index(target)
    section = script[start:start + 1200]

    assert (
        '"semantic-clothing-advice"'
        in section
    )
    assert (
        "seenSemanticNodeIds["
        in section
    )
    assert (
        "renderClothingAdviceCard("
        in section
    )


def test_weather_nodes_use_semantic_status_cleanup_class():
    script = dashboard_script()

    umbrella_start = script.index(
        "function renderUmbrellaAdviceCard"
    )
    clothing_start = script.index(
        "function renderClothingAdviceCard"
    )

    umbrella_section = script[
        umbrella_start:
        clothing_start
    ]

    clothing_section = script[
        clothing_start:
        script.index(
            "function updateSemanticDashboard",
            clothing_start,
        )
    ]

    assert (
        'item.className = "semantic-status-item"'
        in umbrella_section
    )

    assert (
        'item.className = "semantic-status-item"'
        in clothing_section
    )


def test_stale_cleanup_runs_after_weather_dispatch():
    script = dashboard_script()

    umbrella_dispatch = script.index(
        "renderUmbrellaAdviceCard("
    )

    clothing_dispatch = script.index(
        "renderClothingAdviceCard("
    )

    cleanup = script.index(
        "removeStaleSemanticStatusItems(",
        max(
            umbrella_dispatch,
            clothing_dispatch,
        ),
    )

    assert cleanup > umbrella_dispatch
    assert cleanup > clothing_dispatch


def test_weather_nodes_are_not_unconditionally_seen():
    script = dashboard_script()

    normalized = " ".join(
        script.split()
    )

    umbrella_target = (
        'cards[i].target === "umbrella_advice"'
    )
    clothing_target = (
        'cards[i].target === "clothing_advice"'
    )

    assert umbrella_target in normalized
    assert clothing_target in normalized

    umbrella_index = normalized.index(
        umbrella_target
    )
    umbrella_seen = normalized.index(
        "seenSemanticNodeIds[",
        umbrella_index,
    )

    clothing_index = normalized.index(
        clothing_target
    )
    clothing_seen = normalized.index(
        "seenSemanticNodeIds[",
        clothing_index,
    )

    assert umbrella_seen > umbrella_index
    assert clothing_seen > clothing_index

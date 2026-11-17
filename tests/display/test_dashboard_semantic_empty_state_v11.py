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


def test_semantic_dashboard_has_empty_state_renderer():
    script = dashboard_script()

    assert "renderSemanticEmptyState" in script


def test_semantic_empty_state_has_stable_node_id():
    script = dashboard_script()

    assert '"semantic-status-empty"' in script


def test_semantic_empty_state_explains_missing_data():
    script = dashboard_script()

    assert '"暂无可用环境状态"' in script


def test_semantic_empty_state_is_shown_when_no_nodes_seen():
    script = dashboard_script()

    normalized = " ".join(
        script.split()
    )

    assert (
        "Object.keys(seenSemanticNodeIds).length === 0"
        in normalized
    )


def test_semantic_empty_state_is_removed_when_data_returns():
    script = dashboard_script()

    assert "removeSemanticEmptyState" in script


def test_semantic_empty_state_is_not_a_semantic_status_item():
    script = dashboard_script()

    start = script.index(
        "function renderSemanticEmptyState"
    )

    section = script[
        start:start + 900
    ]

    assert (
        'className = "semantic-status-empty"'
        in section
    )

    assert (
        'className = "semantic-status-item"'
        not in section
    )


def dashboard_css():
    return (
        PROJECT
        / "src"
        / "smartscreen_display"
        / "static"
        / "dashboard.css"
    ).read_text(
        encoding="utf-8"
    )


def test_semantic_empty_state_has_dedicated_css():
    css = dashboard_css()

    assert ".semantic-status-empty" in css


def test_semantic_empty_state_is_visually_subordinate():
    css = dashboard_css()

    start = css.index(
        ".semantic-status-empty"
    )
    section = css[start:start + 500]

    assert "font-weight: normal" in section
    assert "font-size:" in section
    assert "color:" in section

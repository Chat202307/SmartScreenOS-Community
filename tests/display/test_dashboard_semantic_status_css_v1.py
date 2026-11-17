from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]

DASHBOARD_CSS = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "static"
    / "dashboard.css"
)


def dashboard_css():
    return DASHBOARD_CSS.read_text(
        encoding="utf-8"
    )


def test_semantic_status_list_has_layout_rule():
    css = dashboard_css()

    assert "#semantic-status-list" in css


def test_semantic_status_item_has_visual_rule():
    css = dashboard_css()

    assert ".semantic-status-item" in css


def test_semantic_status_item_uses_readable_font_size():
    css = dashboard_css()

    start = css.index(".semantic-status-item")
    section = css[start:start + 300]

    assert "font-size: 20px" in section


def test_semantic_status_item_has_vertical_spacing():
    css = dashboard_css()

    start = css.index(".semantic-status-item")
    section = css[start:start + 300]

    assert "padding:" in section


def test_semantic_status_items_have_separator():
    css = dashboard_css()

    assert "border-bottom:" in css[
        css.index(".semantic-status-item"):
    ]

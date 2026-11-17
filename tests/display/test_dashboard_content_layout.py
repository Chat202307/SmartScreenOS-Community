from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def test_dashboard_has_primary_panel():
    html = dashboard_html()

    assert 'class="primary-panel"' in html


def test_dashboard_has_content_panel():
    html = dashboard_html()

    assert 'class="content-panel"' in html


def test_dashboard_has_content_container():
    html = dashboard_html()

    assert 'id="dashboard-content"' in html


def test_content_panel_has_layout():
    css = dashboard_css()

    assert ".content-panel" in css


def test_content_panel_has_minimum_height():
    css = dashboard_css()

    assert "min-height:" in css

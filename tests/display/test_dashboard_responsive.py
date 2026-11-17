from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def test_dashboard_has_viewport_meta():
    html = dashboard_html()

    assert 'name="viewport"' in html
    assert "width=device-width" in html


def test_dashboard_has_responsive_media_query():
    css = dashboard_css()

    assert "@media" in css


def test_dashboard_supports_tablet_width():
    css = dashboard_css()

    assert "max-width: 1024px" in css


def test_dashboard_supports_compact_width():
    css = dashboard_css()

    assert "max-width: 768px" in css


def test_responsive_layout_adjusts_dashboard():
    css = dashboard_css()

    assert ".dashboard" in css


def test_responsive_layout_adjusts_cards():
    css = dashboard_css()

    assert ".dashboard-cards" in css


def test_responsive_layout_adjusts_clock():
    css = dashboard_css()

    assert "#time" in css


def test_responsive_layout_adjusts_photo():
    css = dashboard_css()

    assert "#photo-image" in css

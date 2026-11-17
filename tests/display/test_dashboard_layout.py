from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_dashboard_has_viewport():
    html = dashboard_html()

    assert 'name="viewport"' in html


def test_dashboard_has_main_layout():
    html = dashboard_html()

    assert 'class="dashboard"' in html
    assert 'class="clock-panel"' in html
    assert 'class="weather-panel"' in html


def test_dashboard_has_large_clock_style():
    css = dashboard_css()

    assert "#time" in css
    assert "font-size:" in css


def test_dashboard_has_dark_background():
    css = dashboard_css()

    assert "background:" in css


def test_dashboard_avoids_modern_frameworks():
    html = dashboard_html()
    css = dashboard_css()
    script = dashboard_js()

    combined = html + css + script

    assert "React" not in combined
    assert "Vue" not in combined
    assert "bootstrap" not in combined.lower()


def test_dashboard_keeps_legacy_xhr():
    script = dashboard_js()

    assert "XMLHttpRequest" in script

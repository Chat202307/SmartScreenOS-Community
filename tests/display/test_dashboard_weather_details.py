from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = Path("src/smartscreen_display/static")


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def dashboard_css():
    return (
        STATIC_DIR / "dashboard.css"
    ).read_text(encoding="utf-8")


def test_dashboard_has_wind_field():
    html = dashboard_html()

    assert 'id="wind"' in html


def test_dashboard_reads_wind_speed():
    script = dashboard_js()

    assert "weather.wind_speed" in script
    assert "weather.wind_speed_unit" in script


def test_dashboard_displays_wind_label():
    script = dashboard_js()

    assert "风速" in script


def test_weather_details_have_layout():
    html = dashboard_html()
    css = dashboard_css()

    assert 'class="weather-details"' in html
    assert ".weather-details" in css


def test_weather_details_remain_legacy_compatible():
    script = dashboard_js()

    assert "=>" not in script
    assert "const " not in script
    assert "let " not in script


def test_dashboard_has_weather_icon_node():
    html = dashboard_html()

    assert 'id="weather-icon"' in html
    assert 'class="weather-icon weather-icon-cloudy"' in html


def test_weather_icon_has_sunny_and_cloudy_presentations():
    css = dashboard_css()

    assert ".weather-icon-sunny" in css
    assert ".weather-icon-cloudy:before" in css
    assert ".weather-icon-cloudy:after" in css

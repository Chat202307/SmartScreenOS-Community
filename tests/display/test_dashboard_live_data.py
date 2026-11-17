from pathlib import Path

from src.smartscreen_display.dashboard import DASHBOARD_HTML


STATIC_DIR = (
    Path("src/smartscreen_display/static")
)


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_dashboard_requests_runtime_snapshot():
    script = dashboard_js()

    assert "XMLHttpRequest" in script
    assert 'open("GET", "/api/snapshot", true)' in script


def test_dashboard_has_clock_fields():
    html = dashboard_html()

    assert 'id="time"' in html
    assert 'id="date"' in html


def test_dashboard_has_weather_fields():
    html = dashboard_html()

    assert 'id="condition"' in html
    assert 'id="temperature"' in html
    assert 'id="humidity"' in html


def test_dashboard_reads_clock_capability():
    script = dashboard_js()

    assert "session-clock-main" in script


def test_dashboard_reads_weather_status():
    script = dashboard_js()

    assert '"weather_status"' in script
    assert (
        'capabilities["session-weather-main"]'
        not in script
    )

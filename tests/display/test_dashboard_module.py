from src.smartscreen_display.dashboard import (
    DASHBOARD_HTML,
)


def test_dashboard_html_is_bytes():
    assert isinstance(DASHBOARD_HTML, bytes)


def test_dashboard_html_contains_document():
    html = DASHBOARD_HTML.decode("utf-8")

    assert "<!doctype html>" in html.lower()
    assert "<title>SmartScreenOS</title>" in html


def test_dashboard_html_contains_live_data_elements():
    html = DASHBOARD_HTML.decode("utf-8")

    assert 'id="time"' in html
    assert 'id="date"' in html
    assert 'id="condition"' in html
    assert 'id="temperature"' in html
    assert 'id="humidity"' in html
    assert 'id="update-status"' in html

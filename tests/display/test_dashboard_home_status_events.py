from pathlib import Path


STATIC_DIR = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "smartscreen_display"
    / "static"
)


def dashboard_js():
    return (
        STATIC_DIR / "dashboard.js"
    ).read_text(encoding="utf-8")


def test_dashboard_subscribes_to_home_status_events():
    script = dashboard_js()

    assert "EventSource" in script
    assert '"/api/home/events"' in script


def test_home_status_event_refreshes_home_status_card():
    script = dashboard_js()

    assert (
        'addEventListener('
        '"home-status-changed"'
        in script
    )

    assert "updateHomeStatusCard();" in script


def test_dashboard_keeps_home_status_polling_fallback():
    script = dashboard_js()

    assert (
        "setInterval("
        "updateHomeStatusCard, 5000"
        ");"
        in script
    )


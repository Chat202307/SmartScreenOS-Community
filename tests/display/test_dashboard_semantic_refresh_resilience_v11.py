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


def test_semantic_refresh_tracks_sse_connection_state():
    script = dashboard_script()

    assert "dashboardStateEventsConnected" in script


def test_semantic_event_open_marks_connection_active():
    script = dashboard_script()

    start = script.index(
        "function subscribeDashboardStateEvents"
    )
    section = script[start:start + 1000]

    assert "eventSource.onopen" in section
    assert "dashboardStateEventsConnected = true" in section


def test_semantic_event_error_marks_connection_inactive():
    script = dashboard_script()

    start = script.index(
        "function subscribeDashboardStateEvents"
    )
    section = script[start:start + 1200]

    assert "eventSource.onerror" in section
    assert "dashboardStateEventsConnected = false" in section


def test_semantic_refresh_uses_fast_fallback_when_sse_disconnected():
    script = dashboard_script()

    assert "SEMANTIC_FALLBACK_INTERVAL_MS = 5000" in script


def test_semantic_refresh_uses_slow_safety_poll_when_sse_connected():
    script = dashboard_script()

    assert "SEMANTIC_CONNECTED_INTERVAL_MS = 30000" in script


def test_semantic_refresh_scheduler_chooses_interval_from_connection_state():
    script = dashboard_script()

    assert "scheduleSemanticDashboardRefresh" in script
    assert "dashboardStateEventsConnected" in script
    assert "SEMANTIC_CONNECTED_INTERVAL_MS" in script
    assert "SEMANTIC_FALLBACK_INTERVAL_MS" in script


def test_semantic_refresh_scheduler_replaces_existing_timer():
    script = dashboard_script()

    start = script.index(
        "function scheduleSemanticDashboardRefresh"
    )
    section = script[start:start + 900]

    assert "semanticDashboardRefreshTimer !== null" in section
    assert "clearTimeout(" in section
    assert "semanticDashboardRefreshTimer" in section

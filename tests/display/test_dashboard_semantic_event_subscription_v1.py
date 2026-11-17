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


def test_dashboard_subscribes_to_semantic_events():
    script = dashboard_script()

    assert '"/api/dashboard/events"' in script


def test_dashboard_listens_for_dashboard_state_changed():
    script = dashboard_script()

    assert '"dashboard-state-changed"' in script


def test_dashboard_event_refreshes_semantic_dashboard():
    script = dashboard_script()

    start = script.index(
        "function subscribeDashboardStateEvents"
    )
    section = script[start:start + 700]

    assert "updateSemanticDashboard()" in section


def test_dashboard_starts_semantic_event_subscription():
    script = dashboard_script()

    assert "subscribeDashboardStateEvents();" in script


def test_semantic_polling_remains_as_fallback():
    script = dashboard_script()

    assert (
        "SEMANTIC_FALLBACK_INTERVAL_MS = 5000"
        in script
    )
    assert "scheduleSemanticDashboardRefresh" in script

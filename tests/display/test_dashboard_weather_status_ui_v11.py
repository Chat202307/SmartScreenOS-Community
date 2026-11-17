from pathlib import Path


DASHBOARD_JS = Path(
    "src/smartscreen_display/static/dashboard.js"
)


def dashboard_script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def semantic_section(script):
    start = script.index(
        "function updateSemanticDashboard"
    )
    end = script.index(
        "function scheduleSemanticDashboardRefresh"
    )
    return script[start:end]


def snapshot_section(script):
    start = script.index(
        "function updateDashboard"
    )
    end = script.index(
        "function semanticStatusNodeId"
    )
    return script[start:end]


def test_semantic_dashboard_reads_weather_status():
    section = semantic_section(
        dashboard_script()
    )

    assert '"weather_status"' in section


def test_weather_status_updates_condition():
    section = semantic_section(
        dashboard_script()
    )

    assert (
        'document.getElementById("condition")'
        in section
    )
    assert "weather.condition" in section


def test_weather_status_updates_temperature():
    section = semantic_section(
        dashboard_script()
    )

    assert (
        'document.getElementById("temperature")'
        in section
    )
    assert "weather.temperature" in section


def test_weather_status_updates_humidity():
    section = semantic_section(
        dashboard_script()
    )

    assert (
        'document.getElementById("humidity")'
        in section
    )
    assert "weather.humidity" in section


def test_weather_status_updates_wind():
    section = semantic_section(
        dashboard_script()
    )

    assert (
        'document.getElementById("wind")'
        in section
    )
    assert "weather.wind_speed" in section
    assert "weather.wind_speed_unit" in section


def test_snapshot_dashboard_no_longer_reads_runtime_weather():
    section = snapshot_section(
        dashboard_script()
    )

    assert (
        'capabilities["session-weather-main"]'
        not in section
    )


def test_snapshot_dashboard_still_updates_clock():
    section = snapshot_section(
        dashboard_script()
    )

    assert (
        'capabilities["session-clock-main"]'
        in section
    )
    assert (
        'document.getElementById("time")'
        in section
    )
    assert (
        'document.getElementById("date")'
        in section
    )


def test_weather_status_uses_dashboard_card_updated_at():
    section = semantic_section(
        dashboard_script()
    )

    assert "cards[i].updated_at" in section
    assert "formatObservedAt" in section
    assert "setUpdateStatus(" in section
    assert '"fresh"' in section
    assert '"更新于 "' in section


def test_weather_updated_at_is_converted_to_browser_local_time():
    script = dashboard_script()

    assert "new Date(value)" in script
    assert ".getHours()" in script
    assert ".getMinutes()" in script


def test_weather_updated_at_does_not_slice_iso_utc_time():
    script = dashboard_script()

    assert "value.substring(11, 16)" not in script

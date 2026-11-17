from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]

DASHBOARD_HTML = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "dashboard.py"
)

DASHBOARD_JS = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "static"
    / "dashboard.js"
)


def dashboard_html():
    return DASHBOARD_HTML.read_text(
        encoding="utf-8"
    )


def dashboard_script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def test_dashboard_has_generic_observation_container():
    html = dashboard_html()

    assert 'id="observation-status-list"' in html
    assert "传感器数据" in html


def test_dashboard_reads_observations_from_dashboard_api():
    script = dashboard_script()

    assert "payload.observations" in script
    assert "renderGenericObservations" in script


def test_generic_observation_renderer_handles_illuminance():
    script = dashboard_script()

    start = script.index(
        "function renderGenericObservations"
    )
    section = script[start:start + 2600]

    assert '"illuminance"' in section
    assert '"光照度"' in section


def test_generic_observation_renderer_handles_motion_idle_seconds():
    script = dashboard_script()

    start = script.index(
        "function renderGenericObservations"
    )
    section = script[start:start + 2600]

    assert '"motion_idle_seconds"' in section
    assert '"无移动持续"' in section
    assert '"秒"' in section


def test_generic_observation_renderer_uses_location_label():
    script = dashboard_script()

    start = script.index(
        "function renderGenericObservations"
    )
    section = script[start:start + 2600]

    assert "location_label" in section
    assert "location_id" in section


def generic_observation_renderer_section():
    script = dashboard_script()

    start = script.index(
        "function renderGenericObservations"
    )

    end = script.index(
        "function updateSemanticDashboard",
        start,
    )

    return script[start:end]


def test_generic_observation_renderer_handles_temperature():
    section = (
        generic_observation_renderer_section()
    )

    assert '"temperature"' in section
    assert '"温度"' in section
    assert '"degC"' in section
    assert '"°C"' in section


def test_generic_observation_renderer_handles_humidity():
    section = (
        generic_observation_renderer_section()
    )

    assert '"humidity"' in section
    assert '"湿度"' in section
    assert '"percent"' in section
    assert '"%"' in section


def test_generic_observation_renderer_handles_pm25():
    section = (
        generic_observation_renderer_section()
    )

    assert '"pm25"' in section
    assert '"PM2.5"' in section


def test_generic_observation_renderer_handles_hcho():
    section = (
        generic_observation_renderer_section()
    )

    assert '"hcho"' in section
    assert '"甲醛"' in section

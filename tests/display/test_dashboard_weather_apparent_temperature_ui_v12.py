from pathlib import Path

from src.smartscreen_display.dashboard import (
    DASHBOARD_HTML,
)


DASHBOARD_JS = Path(
    "src/smartscreen_display/static/dashboard.js"
)

DASHBOARD_CSS = Path(
    "src/smartscreen_display/static/dashboard.css"
)


def dashboard_html():
    return DASHBOARD_HTML.decode("utf-8")


def dashboard_script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def dashboard_style():
    return DASHBOARD_CSS.read_text(
        encoding="utf-8"
    )


def test_dashboard_has_apparent_temperature_field():
    html = dashboard_html()

    assert 'id="apparent-temperature"' in html


def test_weather_status_reads_apparent_temperature():
    script = dashboard_script()

    assert "weather.apparent_temperature" in script


def test_weather_status_displays_apparent_temperature_label():
    script = dashboard_script()

    assert '"体感 "' in script


def test_weather_status_displays_apparent_temperature_unit():
    script = dashboard_script()

    assert (
        "weather.apparent_temperature_unit"
        in script
    )


def test_weather_details_styles_apparent_temperature():
    style = dashboard_style()

    assert "#apparent-temperature" in style


def test_weather_apparent_temperature_is_legacy_browser_safe():
    script = dashboard_script()

    assert "=>" not in script
    assert "const " not in script
    assert "let " not in script


def test_apparent_temperature_is_rounded_to_one_decimal():
    script = dashboard_script()

    assert (
        "weather.apparent_temperature.toFixed(1)"
        in script
    )


def test_apparent_temperature_does_not_render_raw_float():
    script = dashboard_script()

    assert (
        '"体感 " +\n'
        '                weather.apparent_temperature +'
        not in script
    )


def test_apparent_temperature_formats_degc_as_degree_celsius():
    script = dashboard_script()

    assert (
        'weather.apparent_temperature_unit === "degC"'
        in script
    )
    assert '"°C"' in script


def test_apparent_temperature_does_not_render_internal_degc_unit_directly():
    script = dashboard_script()

    assert (
        'weather.apparent_temperature_unit\n'
        '                  || "°C"'
        not in script
    )

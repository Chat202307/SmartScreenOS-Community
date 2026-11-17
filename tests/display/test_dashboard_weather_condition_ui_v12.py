from pathlib import Path


DASHBOARD_JS = Path(
    "src/smartscreen_display/static/dashboard.js"
)


def dashboard_script():
    return DASHBOARD_JS.read_text(
        encoding="utf-8"
    )


def test_dashboard_has_weather_condition_formatter():
    script = dashboard_script()

    assert "formatWeatherCondition" in script


def test_weather_condition_maps_common_states():
    script = dashboard_script()

    expected = {
        '"sunny"': '"晴"',
        '"clear-night"': '"晴夜"',
        '"partlycloudy"': '"多云"',
        '"cloudy"': '"阴"',
        '"rainy"': '"雨"',
        '"pouring"': '"大雨"',
        '"lightning"': '"雷电"',
        '"lightning-rainy"': '"雷雨"',
        '"snowy"': '"雪"',
        '"snowy-rainy"': '"雨夹雪"',
        '"fog"': '"雾"',
        '"hail"': '"冰雹"',
        '"windy"': '"大风"',
        '"windy-variant"': '"多风"',
        '"exceptional"': '"异常天气"',
    }

    for source, label in expected.items():
        assert source in script
        assert label in script


def test_weather_status_uses_condition_formatter():
    script = dashboard_script()

    assert (
        "formatWeatherCondition("
        in script
    )

    assert (
        "weather.condition ||"
        not in script
    )


def test_unknown_weather_condition_has_safe_fallback():
    script = dashboard_script()

    assert 'return value || "--";' in script


def test_weather_condition_formatter_is_legacy_browser_safe():
    script = dashboard_script()

    assert "=>" not in script
    assert "const " not in script
    assert "let " not in script


def test_dashboard_weather_icon_follows_condition():
    script = dashboard_script()

    assert "weatherIconClass" in script
    assert '"weather-icon-sunny"' in script
    assert '"weather-icon-cloudy"' in script
    assert (
        'document.getElementById("weather-icon")'
        in script
    )


def test_sunny_weather_uses_sunny_icon():
    script = dashboard_script()

    assert 'value === "sunny"' in script
    assert 'return "weather-icon-sunny";' in script

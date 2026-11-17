from src.smartscreen_runtime.runtime.engine import RuntimeEngine


def test_start_overrides_manifest_configuration():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
        configuration={
            "timezone": "UTC",
            "timeFormat": "12h",
        },
    )

    instance = engine.get_instance(session.session_id)

    assert instance.context is not None
    assert instance.context.configuration["timezone"] == "UTC"
    assert instance.context.configuration["timeFormat"] == "12h"

    engine.stop(session.session_id)


def test_start_preserves_unmodified_manifest_values():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/weather")

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
        configuration={
            "location": "101010100",
        },
    )

    instance = engine.get_instance(session.session_id)

    assert instance.context is not None
    assert instance.context.configuration["location"] == "101010100"
    assert (
        instance.context.configuration["temperatureUnit"]
        == "celsius"
    )

    engine.stop(session.session_id)


def test_configuration_override_does_not_mutate_manifest():
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    original_configuration = dict(
        capability.manifest.configuration
    )

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
        configuration={
            "timezone": "UTC",
            "timeFormat": "12h",
        },
    )

    assert (
        capability.manifest.configuration
        == original_configuration
    )

    engine.stop(session.session_id)


def test_weather_can_receive_qweather_configuration(
    monkeypatch,
):
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_API_HOST",
        "abc1234xyz.def.qweatherapi.com",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_API_KEY",
        "test-api-key",
    )

    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/weather")

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
        configuration={
            "location": "101010100",
            "provider": "qweather",
            "language": "zh",
        },
    )

    weather = engine.get_instance(session.session_id)

    assert weather.provider is not None
    assert weather.context.configuration["location"] == "101010100"
    assert weather.context.configuration["provider"] == "qweather"

    engine.stop(session.session_id)

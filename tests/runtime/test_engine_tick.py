from datetime import datetime, timezone

from src.smartscreen_runtime.runtime.engine import RuntimeEngine


class FakeWeatherProvider:
    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, location: str) -> dict:
        self.calls += 1

        return {
            "condition": "sunny",
            "temperature": 25.0,
            "humidity": 50,
            "windSpeed": 10.0,
            "observedAt": datetime(
                2026,
                8,
                7,
                8,
                0,
                tzinfo=timezone.utc,
            ),
        }


def start_weather():
    engine = RuntimeEngine()

    capability = engine.install(
        "examples/capabilities/weather"
    )

    session = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
        configuration={
            "location": "Dalian",
            "temperatureUnit": "celsius",
            "refreshIntervalSeconds": 900,
        },
    )

    weather = engine.get_instance(session.session_id)

    provider = FakeWeatherProvider()
    weather.set_provider(provider)

    return engine, session, weather, provider


def test_tick_refreshes_weather_without_cache():
    engine, session, weather, provider = start_weather()

    engine.tick()

    assert provider.calls == 1
    assert weather.snapshot()["temperature"] == 25.0

    engine.stop(session.session_id)


def test_tick_does_not_refresh_fresh_weather():
    engine, session, weather, provider = start_weather()

    engine.tick()
    engine.tick()

    assert provider.calls == 1

    engine.stop(session.session_id)


def test_tick_ignores_stopped_sessions():
    engine, session, weather, provider = start_weather()

    engine.stop(session.session_id)

    engine.tick()

    assert provider.calls == 0


def test_tick_handles_multiple_running_sessions():
    engine = RuntimeEngine()

    capability = engine.install(
        "examples/capabilities/weather"
    )

    first = engine.start(
        capability.capability_id,
        session_id="session-weather-001",
        configuration={
            "location": "Dalian",
            "refreshIntervalSeconds": 900,
        },
    )

    second = engine.start(
        capability.capability_id,
        session_id="session-weather-002",
        configuration={
            "location": "Dalian",
            "refreshIntervalSeconds": 900,
        },
    )

    first_weather = engine.get_instance(first.session_id)
    second_weather = engine.get_instance(second.session_id)

    first_provider = FakeWeatherProvider()
    second_provider = FakeWeatherProvider()

    first_weather.set_provider(first_provider)
    second_weather.set_provider(second_provider)

    engine.tick()

    assert first_provider.calls == 1
    assert second_provider.calls == 1

    engine.stop(first.session_id)
    engine.stop(second.session_id)

from src.smartscreen_display.application import (
    run_display_server,
)


class FakeRuntime:
    def start_background(self):
        pass

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


class FakeServer:
    def serve_forever(self):
        raise KeyboardInterrupt

    def server_close(self):
        pass


def test_application_wires_weather_forecast_source(
    monkeypatch,
):
    captured = {}

    class FakeProvider:
        pass

    class FakeForecastSource:
        def __init__(
            self,
            *,
            base_url,
            token,
            entity_id,
            adapter,
            observation_accumulator,
            observation_sink,
        ):
            captured["base_url"] = base_url
            captured["token"] = token
            captured["entity_id"] = entity_id
            captured["adapter"] = adapter
            captured["accumulator"] = (
                observation_accumulator
            )
            captured["sink"] = observation_sink

        def start(self):
            captured["started"] = True

        def stop(self):
            captured["stopped"] = True

        def join(self, timeout=None):
            captured["joined"] = timeout

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://ha.local",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantWeatherForecastSource",
        FakeForecastSource,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=lambda *args, **kwargs: FakeServer(),
    )

    assert captured["base_url"] == "http://ha.local"
    assert captured["token"] == "secret"
    assert (
        captured["entity_id"]
        == "weather.demo_entity_065"
    )
    assert captured["adapter"] is not None
    assert captured["accumulator"] is not None
    assert captured["sink"] is not None

    assert captured["started"] is True
    assert captured["stopped"] is True
    assert captured["joined"] == 5.0

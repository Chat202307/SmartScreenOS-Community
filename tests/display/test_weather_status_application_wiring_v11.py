from src.smartscreen_platform.capabilities.weather_status import (
    WeatherStatusCapability,
)

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


def test_application_wires_weather_status_capability(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        '{"entities":[]}',
        encoding="utf-8",
    )

    class FakePipeline:
        def __init__(
            self,
            *,
            household_state,
            interpreters,
            capabilities,
            knowledge=None,
        ):
            captured["capabilities"] = (
                capabilities
            )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "PlatformStatePipeline",
        FakePipeline,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: None,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
    )

    assert any(
        isinstance(
            capability,
            WeatherStatusCapability,
        )
        for capability in captured["capabilities"]
    )

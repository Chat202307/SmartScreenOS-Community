from src.smartscreen_display.application import run_display_server
from src.smartscreen_platform.household_state import HouseholdStateEngine


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


def test_display_application_wires_household_state_source(
    monkeypatch,
):
    for key in (
        "SMARTSCREEN_XINGOO_TOKEN",
        "SMARTSCREEN_XINGOO_USERNAME",
        "SMARTSCREEN_XINGOO_PASSWORD",
    ):
        monkeypatch.delenv(
            key,
            raising=False,
        )

    captured = {}

    def runtime_factory(config_path):
        return FakeRuntime()

    def server_factory(
        app,
        *,
        host,
        port,
        home_status_notifier=None,
        dashboard_state_notifier=None,
    ):
        captured["app"] = app
        return FakeServer()

    result = run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
        home_file="home.json",
    )

    assert result == 0

    app = captured["app"]

    assert isinstance(
        app._household_state_source,
        HouseholdStateEngine,
    )


def test_display_application_accepts_injected_household_state_source(monkeypatch):
    for key in (
        "SMARTSCREEN_XINGOO_TOKEN",
        "SMARTSCREEN_XINGOO_USERNAME",
        "SMARTSCREEN_XINGOO_PASSWORD",
    ):
        monkeypatch.delenv(
            key,
            raising=False,
        )

    captured = {}
    household_state = HouseholdStateEngine()

    def runtime_factory(config_path):
        return FakeRuntime()

    def server_factory(
        app,
        *,
        host,
        port,
        home_status_notifier=None,
        dashboard_state_notifier=None,
    ):
        captured["app"] = app
        return FakeServer()

    result = run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
        home_file="home.json",
        household_state_source=household_state,
    )

    assert result == 0
    assert (
        captured["app"]._household_state_source
        is household_state
    )


def test_display_application_wires_dashboard_state_notifier(
    monkeypatch,
):
    for key in (
        "SMARTSCREEN_XINGOO_TOKEN",
        "SMARTSCREEN_XINGOO_USERNAME",
        "SMARTSCREEN_XINGOO_PASSWORD",
    ):
        monkeypatch.delenv(
            key,
            raising=False,
        )

    captured = {}

    def runtime_factory(config_path):
        return FakeRuntime()

    def server_factory(
        app,
        *,
        host,
        port,
        home_status_notifier=None,
        dashboard_state_notifier=None,
    ):
        captured["app"] = app
        captured["dashboard_state_notifier"] = (
            dashboard_state_notifier
        )
        return FakeServer()

    result = run_display_server(
        runtime_factory=runtime_factory,
        server_factory=server_factory,
        home_file="home.json",
    )

    assert result == 0
    assert (
        captured["dashboard_state_notifier"]
        is not None
    )

    assert (
        captured["app"]
        ._household_state_source
        ._change_notifier
        is captured["dashboard_state_notifier"]
    )

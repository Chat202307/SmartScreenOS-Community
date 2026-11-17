import json

import pytest

from src.smartscreen_display.application import (
    run_display_server,
)


@pytest.fixture(autouse=True)
def isolate_xingoo_environment(
    monkeypatch,
):
    for variable in (
        "SMARTSCREEN_XINGOO_TOKEN",
        "SMARTSCREEN_XINGOO_USERNAME",
        "SMARTSCREEN_XINGOO_PASSWORD",
    ):
        monkeypatch.delenv(
            variable,
            raising=False,
        )


class FakeRuntime:
    def start_background(self):
        pass

    def stop_background(self):
        pass

    def join_background(self):
        pass

    def stop(self):
        pass

    def join(
        self,
        timeout=None,
    ):
        pass


class FakeServer:
    def serve_forever(self):
        pass

    def shutdown(self):
        pass

    def server_close(self):
        pass


def test_display_application_wires_user_room_names(
    tmp_path,
):
    home_config = tmp_path / "home.json"

    home_config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rooms": [
                    {
                        "id": "living",
                        "name": "用户命名的家庭活动室",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(
        app,
        *,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=server_factory,
        home_file="home-status.json",
        location_config_file=home_config,
    )

    builder = (
        captured["app"]._presentation_builder
    )

    assert builder._location_labels == {
        "living": "用户命名的家庭活动室",
    }


def test_display_application_defaults_location_config_to_home_config():
    captured = {}

    def server_factory(
        app,
        *,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=server_factory,
        home_file="home-status.json",
    )

    assert (
        captured["app"]
        ._presentation_builder
        ._location_labels
        is not None
    )


def test_display_application_wires_user_room_order(
    tmp_path,
):
    home_config = tmp_path / "home.json"

    home_config.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "rooms": [
                    {
                        "id": "living",
                        "name": "家庭活动室",
                        "order": 40,
                    },
                    {
                        "id": "study",
                        "name": "阅读室",
                        "order": 10,
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(
        app,
        *,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=server_factory,
        home_file="home-status.json",
        location_config_file=home_config,
    )

    builder = (
        captured["app"]
        ._presentation_builder
    )

    assert builder._location_orders == {
        "living": 40,
        "study": 10,
    }


def test_display_application_room_order_is_optional(
    tmp_path,
):
    home_config = tmp_path / "home.json"

    home_config.write_text(
        json.dumps(
            {
                "rooms": [
                    {
                        "id": "living",
                        "name": "家庭活动室",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    captured = {}

    def server_factory(
        app,
        *,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=server_factory,
        home_file="home-status.json",
        location_config_file=home_config,
    )

    assert (
        captured["app"]
        ._presentation_builder
        ._location_orders
        == {}
    )

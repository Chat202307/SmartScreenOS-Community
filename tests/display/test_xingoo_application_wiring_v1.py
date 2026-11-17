import pytest

from pathlib import Path

from src.smartscreen_display.application import (
    run_display_server,
)



@pytest.fixture(autouse=True)
def isolate_xingoo_password_environment(
    monkeypatch,
):
    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_PASSWORD",
        raising=False,
    )


class FakeRuntime:
    def start_background(self):
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

    def server_close(self):
        pass


def test_application_constructs_xingoo_source_from_device_config(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.air_1",
      "name": "空气净化器",
      "location_id": "living",
      "adapter_id": "xingoo",
      "parameters": {
        "pm25": {
          "source_id": "iot-123:PM25",
          "value_type": "float"
        },
        "temperature": {
          "source_id": "iot-123:CurrentTemperature",
          "value_type": "float",
          "unit": "degC"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        "token-123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        "13800138000",
    )

    class FakeClient:
        def __init__(
            self,
            *,
            token,
            username,
        ):
            captured["token"] = token
            captured["username"] = (
                username
            )

    class FakeAdapter:
        def __init__(
            self,
            *,
            registry,
            ingestion,
        ):
            captured["registry"] = (
                registry
            )
            captured["ingestion"] = (
                ingestion
            )

    class FakeSource:
        def __init__(
            self,
            *,
            client,
            adapter,
            iot_ids,
            observation_accumulator,
            observation_sink,
        ):
            captured["client"] = client
            captured["adapter"] = adapter
            captured["iot_ids"] = list(
                iot_ids
            )
            captured["accumulator"] = (
                observation_accumulator
            )
            captured["sink"] = (
                observation_sink
            )

        def start(self):
            pass

        def stop(self):
            pass

        def join(
            self,
            timeout=None,
        ):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooClient",
        FakeClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataSource",
        FakeSource,
    )

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            lambda *args, **kwargs:
            FakeServer()
        ),
        device_data_file=(
            device_config
        ),
    )

    assert captured["token"] == (
        "token-123"
    )

    assert captured["username"] == (
        "13800138000"
    )

    assert captured["iot_ids"] == [
        "iot-123"
    ]

    assert captured["registry"] is not None
    assert captured["ingestion"] is not None
    assert captured["accumulator"] is not None
    assert captured["sink"] is not None


def test_application_does_not_construct_xingoo_without_credentials(
    monkeypatch,
    tmp_path,
):
    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.air_1",
      "name": "空气净化器",
      "location_id": "living",
      "adapter_id": "xingoo",
      "parameters": {
        "pm25": {
          "source_id": "iot-123:PM25",
          "value_type": "float"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        raising=False,
    )

    def fail_source(**kwargs):
        raise AssertionError(
            "Xingoo source must not "
            "be constructed"
        )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataSource",
        fail_source,
    )

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            lambda *args, **kwargs:
            FakeServer()
        ),
        device_data_file=(
            device_config
        ),
    )


def test_application_starts_and_stops_xingoo_source(
    monkeypatch,
    tmp_path,
):
    events = []

    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.air_1",
      "name": "空气净化器",
      "location_id": "living",
      "adapter_id": "xingoo",
      "parameters": {
        "pm25": {
          "source_id": "iot-123:PM25",
          "value_type": "float"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        "token-123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        "13800138000",
    )

    class FakeClient:
        def __init__(self, **kwargs):
            pass

    class FakeAdapter:
        def __init__(self, **kwargs):
            pass

    class FakeSource:
        def __init__(self, **kwargs):
            pass

        def start(self):
            events.append(
                "xingoo-start"
            )

        def stop(self):
            events.append(
                "xingoo-stop"
            )

        def join(
            self,
            timeout=None,
        ):
            events.append(
                (
                    "xingoo-join",
                    timeout,
                )
            )

    class InterruptingServer:
        def serve_forever(self):
            events.append(
                "server"
            )
            raise KeyboardInterrupt

        def server_close(self):
            events.append(
                "server-close"
            )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooClient",
        FakeClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataSource",
        FakeSource,
    )

    result = run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            lambda *args, **kwargs:
            InterruptingServer()
        ),
        device_data_file=(
            device_config
        ),
    )

    assert result == 0

    assert (
        "xingoo-start"
        in events
    )

    assert (
        "xingoo-stop"
        in events
    )

    assert (
        (
            "xingoo-join",
            5.0,
        )
        in events
    )

    assert (
        events.index(
            "xingoo-start"
        )
        < events.index(
            "server"
        )
    )

    assert (
        events.index(
            "xingoo-stop"
        )
        < events.index(
            "server-close"
        )
    )


def test_application_constructs_and_passes_xingoo_device_controller(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "xingoo_test_device_1",
      "name": "IAM消毒空气净化器",
      "location_id": "open_public_area",
      "adapter_id": "xingoo",
      "parameters": {
        "temperature": {
          "source_id": "iot-123:CurrentTemperature",
          "value_type": "float",
          "unit": "degC"
        },
        "humidity": {
          "source_id": "iot-123:CurrentHumidity",
          "value_type": "float",
          "unit": "percent"
        },
        "pm25": {
          "source_id": "iot-123:PM25",
          "value_type": "float"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        "token-123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        "13800138000",
    )

    class FakeClient:
        def __init__(
            self,
            *,
            token,
            username,
        ):
            captured["client"] = self
            captured["token"] = token
            captured["username"] = (
                username
            )

    class FakeAdapter:
        def __init__(self, **kwargs):
            pass

    class FakeSource:
        def __init__(self, **kwargs):
            captured["source"] = self

        def start(self):
            pass

        def stop(self):
            pass

        def join(
            self,
            timeout=None,
        ):
            pass

    class FakeController:
        def __init__(
            self,
            *,
            client,
            device_iot_ids,
        ):
            captured["controller"] = self
            captured[
                "controller_client"
            ] = client
            captured[
                "device_iot_ids"
            ] = dict(
                device_iot_ids
            )

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app

        return FakeServer()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooClient",
        FakeClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceController",
        FakeController,
    )

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            server_factory
        ),
        device_data_file=(
            device_config
        ),
    )

    assert captured[
        "device_iot_ids"
    ] == {
        "xingoo_test_device_1":
        "iot-123",
    }

    assert (
        captured["controller_client"]
        is captured["client"]
    )


    assert (
        captured["app"]
        ._device_state_refresher
        is captured["source"]
    )



def test_application_logs_in_with_password_before_constructing_xingoo_components(
    monkeypatch,
    tmp_path,
):
    events = []
    captured = {}

    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "xingoo_test_device_1",
      "name": "IAM消毒空气净化器",
      "location_id": "open_public_area",
      "adapter_id": "xingoo",
      "parameters": {
        "pm25": {
          "source_id": "iot-123:PM25",
          "value_type": "float"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        raising=False,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        "10000000001",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_PASSWORD",
        "test-password",
    )

    class FakeClient:
        def __init__(
            self,
            *,
            token,
            username,
        ):
            events.append(
                "client"
            )

            captured[
                "initial_token"
            ] = token

            captured[
                "username"
            ] = username

            captured[
                "client"
            ] = self

        def login(
            self,
            *,
            password,
        ):
            events.append(
                "login"
            )

            captured[
                "password"
            ] = password

            return {
                "userName":
                    "10000000001",
                "userId":
                    "user-123",
                "token":
                    "fresh-token",
            }

    class FakeAdapter:
        def __init__(
            self,
            **kwargs,
        ):
            events.append(
                "adapter"
            )

    class FakeSource:
        def __init__(
            self,
            *,
            client,
            **kwargs,
        ):
            events.append(
                "source"
            )

            captured[
                "source_client"
            ] = client

        def start(self):
            pass

        def stop(self):
            pass

        def join(
            self,
            timeout=None,
        ):
            pass

    class FakeController:
        def __init__(
            self,
            *,
            client,
            device_iot_ids,
        ):
            events.append(
                "controller"
            )

            captured[
                "controller_client"
            ] = client

            captured[
                "device_iot_ids"
            ] = dict(
                device_iot_ids
            )

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        captured[
            "app"
        ] = app

        return FakeServer()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooClient",
        FakeClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceController",
        FakeController,
    )

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            server_factory
        ),
        device_data_file=(
            device_config
        ),
    )

    assert (
        captured[
            "initial_token"
        ]
        == ""
    )

    assert (
        captured[
            "username"
        ]
        == "10000000001"
    )

    assert (
        captured[
            "password"
        ]
        == "test-password"
    )

    assert (
        events.index(
            "login"
        )
        < events.index(
            "adapter"
        )
    )

    assert (
        events.index(
            "login"
        )
        < events.index(
            "source"
        )
    )

    assert (
        events.index(
            "login"
        )
        < events.index(
            "controller"
        )
    )

    assert (
        captured[
            "source_client"
        ]
        is captured[
            "client"
        ]
    )

    assert (
        captured[
            "controller_client"
        ]
        is captured[
            "client"
        ]
    )

    assert (
        captured[
            "device_iot_ids"
        ]
        == {
            "xingoo_test_device_1":
                "iot-123",
        }
    )


def test_application_constructs_generic_device_control_dispatcher(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "xingoo_test_device_1",
      "name": "IAM消毒空气净化器",
      "location_id": "open_public_area",
      "adapter_id": "xingoo",
      "parameters": {
        "power": {
          "source_id": "iot-123:PowerSwitch",
          "value_type": "bool"
        }
      },
      "controls": {
        "power": {
          "parameter": "power",
          "kind": "boolean"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        "token-123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        "13800138000",
    )

    class FakeClient:
        def __init__(
            self,
            *,
            token,
            username,
        ):
            captured["client"] = self

    class FakeAdapter:
        def __init__(
            self,
            **kwargs,
        ):
            pass

    class FakeSource:
        def __init__(
            self,
            **kwargs,
        ):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(
            self,
            timeout=None,
        ):
            pass

    class FakeController:
        def __init__(
            self,
            *,
            client,
            device_iot_ids,
        ):
            captured["controller"] = self

    class FakeExecutor:
        def __init__(
            self,
            *,
            controller,
        ):
            captured[
                "executor_controller"
            ] = controller

    class FakeDispatcher:
        def __init__(
            self,
            *,
            registry,
            executors,
        ):
            captured["dispatcher"] = self
            captured["registry"] = registry
            captured["executors"] = dict(
                executors
            )

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooClient",
        FakeClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceController",
        FakeController,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "XingooDeviceControlExecutor",
        FakeExecutor,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DeviceControlDispatcher",
        FakeDispatcher,
    )

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            server_factory
        ),
        device_data_file=(
            device_config
        ),
    )

    assert (
        captured[
            "executor_controller"
        ]
        is captured["controller"]
    )

    assert set(
        captured["executors"]
    ) == {
        "xingoo",
    }

    binding = (
        captured["registry"]
        .resolve(
            device_id=(
                "xingoo_test_device_1"
            ),
            control_id="power",
        )
    )

    assert binding is not None
    assert (
        binding.adapter_id
        == "xingoo"
    )

    assert (
        captured["app"]
        ._device_control_dispatcher
        is captured["dispatcher"]
    )


def test_application_constructs_home_assistant_device_control_executor(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        tmp_path
        / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "corridor.light_1",
      "name": "走廊灯",
      "location_id": "corridor",
      "adapter_id": "home_assistant",
      "adapter_config": {
        "entity_id": "light.demo_entity_026"
      },
      "parameters": {
        "power": {
          "source_id": "light.demo_entity_026",
          "value_type": "bool"
        }
      },
      "controls": {
        "power": {
          "parameter": "power",
          "kind": "boolean"
        }
      }
    },
    {
      "device_id": "princess_room.curtain_1",
      "name": "公主房窗帘",
      "location_id": "princess_room",
      "adapter_id": "home_assistant",
      "adapter_config": {
        "entity_id": "cover.demo_entity_019"
      },
      "parameters": {
        "state": {
          "source_id": "cover.demo_entity_019#state",
          "value_type": "string"
        },
        "position": {
          "source_id": "cover.demo_entity_019#position",
          "value_type": "int",
          "unit": "percent"
        }
      },
      "controls": {
        "state": {
          "parameter": "state",
          "kind": "select",
          "options": [
            "open",
            "close",
            "stop"
          ]
        },
        "position": {
          "parameter": "position",
          "kind": "select",
          "options": [
            "0",
            "50",
            "100"
          ]
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://home-assistant.local:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "ha-token",
    )

    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_USERNAME",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_PASSWORD",
        raising=False,
    )

    class FakeHomeAssistantClient:
        def __init__(
            self,
            base_url,
            token,
        ):
            captured[
                "ha_client"
            ] = self
            captured[
                "ha_base_url"
            ] = base_url
            captured[
                "ha_token"
            ] = token

    class FakeHomeAssistantExecutor:
        def __init__(
            self,
            *,
            client,
            device_entity_ids,
            device_adapter_configs=None,
        ):
            captured[
                "ha_executor"
            ] = self
            captured[
                "ha_executor_client"
            ] = client
            captured[
                "ha_device_entity_ids"
            ] = dict(
                device_entity_ids
            )
            captured[
                "ha_device_adapter_configs"
            ] = dict(
                device_adapter_configs
                or {}
            )

    class FakeDispatcher:
        def __init__(
            self,
            *,
            registry,
            executors,
        ):
            captured[
                "dispatcher"
            ] = self
            captured[
                "registry"
            ] = registry
            captured[
                "executors"
            ] = dict(
                executors
            )

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        captured[
            "app"
        ] = app

        return FakeServer()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantClient",
        FakeHomeAssistantClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantDeviceControlExecutor",
        FakeHomeAssistantExecutor,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DeviceControlDispatcher",
        FakeDispatcher,
    )

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=(
            server_factory
        ),
        device_data_file=(
            device_config
        ),
        home_file=(
            tmp_path
            / "home.json"
        ),
    )

    assert (
        captured[
            "ha_base_url"
        ]
        == "http://home-assistant.local:8123"
    )

    assert (
        captured[
            "ha_token"
        ]
        == "ha-token"
    )

    assert (
        captured[
            "ha_executor_client"
        ]
        is captured[
            "ha_client"
        ]
    )

    assert (
        captured[
            "ha_device_entity_ids"
        ]
        == {
            "corridor.light_1": (
                'light.demo_entity_026'
            ),
            "princess_room.curtain_1": (
                'cover.demo_entity_019'
            ),
        }
    )

    assert (
        captured[
            "ha_device_adapter_configs"
        ]
        == {
            "corridor.light_1": {
                "entity_id": (
                    'light.demo_entity_026'
                ),
            },
            "princess_room.curtain_1": {
                "entity_id": (
                    'cover.demo_entity_019'
                ),
            },
        }
    )

    assert set(
        captured[
            "executors"
        ]
    ) == {
        "home_assistant",
    }

    binding = (
        captured[
            "registry"
        ]
        .resolve(
            device_id=(
                "corridor.light_1"
            ),
            control_id="power",
        )
    )

    assert binding is not None

    assert (
        binding.adapter_id
        == "home_assistant"
    )

    cover_binding = (
        captured[
            "registry"
        ]
        .resolve(
            device_id=(
                "princess_room.curtain_1"
            ),
            control_id="position",
        )
    )

    assert cover_binding is not None

    assert (
        cover_binding.adapter_id
        == "home_assistant"
    )

    assert (
        cover_binding.control.parameter
        == "position"
    )

    assert (
        captured[
            "app"
        ]
        ._device_control_dispatcher
        is captured[
            "dispatcher"
        ]
    )

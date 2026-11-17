from src.smartscreen_display.application import (
    run_display_server,
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


def _write_curtain_config(tmp_path):
    path = (
        tmp_path
        / "device_data.json"
    )

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.curtain_1",
      "name": "客厅窗帘",
      "location_id": "living",
      "adapter_id": "dnake_mqtt",
      "adapter_config": {
        "command_topic": "dnake/curtain/客厅窗帘/set"
      },
      "parameters": {
        "state": {
          "source_id": "dnake/curtain/客厅窗帘/state",
          "value_type": "string"
        }
      },
      "controls": {
        "state": {
          "parameter": "state",
          "kind": "select",
          "options": [
            "open",
            "closed",
            "stopped"
          ]
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    return path


def test_runtime_mqtt_auth_precedes_connect_and_preserves_dnake_lifecycle(monkeypatch, tmp_path):
    import paho.mqtt.client as mqtt
    from unittest.mock import Mock
    from src.smartscreen_display import application as module

    client = Mock(spec=mqtt.Client)
    events = []
    client.username_pw_set.side_effect = lambda *args: events.append(("auth", args))
    client.connect.side_effect = lambda *args: events.append(("connect", args))
    client.loop_start.side_effect = lambda: events.append(("loop_start",))
    client.disconnect.side_effect = lambda: events.append(("disconnect",))
    client.loop_stop.side_effect = lambda: events.append(("loop_stop",))
    created = []
    def make_client(version):
        created.append(version)
        return client
    monkeypatch.setattr(module, "DnakeMqttClient", make_client)
    monkeypatch.delenv("SMARTSCREEN_HA_URL", raising=False)
    monkeypatch.delenv("SMARTSCREEN_HA_TOKEN", raising=False)
    monkeypatch.setenv("SMARTSCREEN_DNAKE_MQTT_USERNAME", "test-user")
    monkeypatch.setenv("SMARTSCREEN_DNAKE_MQTT_PASSWORD", "test-only-password")
    monkeypatch.setenv("SMARTSCREEN_DNAKE_MQTT_HOST", "broker.example.invalid")
    monkeypatch.setenv("SMARTSCREEN_DNAKE_MQTT_PORT", "1884")
    captured = {}
    def make_server(app, **kwargs):
        captured["app"] = app
        return FakeServer()
    run_display_server(
        runtime_factory=lambda _: FakeRuntime(), server_factory=make_server,
        device_data_file=_write_curtain_config(tmp_path),
    )
    assert created == [mqtt.CallbackAPIVersion.VERSION2]
    assert events == [("auth", ("test-user", "test-only-password")),
                      ("connect", ("broker.example.invalid", 1884, 60)),
                      ("loop_start",), ("disconnect",), ("loop_stop",)]
    executor = captured["app"]._device_control_dispatcher._executors["dnake_mqtt"]
    assert executor._client is client
    client.on_connect(client, None, {}, 0)
    client.subscribe.assert_called_with("dnake/curtain/客厅窗帘/state")


def test_anonymous_mqtt_preserved_and_partial_credentials_fail_before_connect(monkeypatch, tmp_path):
    import pytest
    import paho.mqtt.client as mqtt
    from unittest.mock import Mock
    from src.smartscreen_display import application as module

    client = Mock(spec=mqtt.Client)
    monkeypatch.setattr(module, "DnakeMqttClient", lambda *args: client)
    monkeypatch.delenv("SMARTSCREEN_HA_URL", raising=False)
    monkeypatch.delenv("SMARTSCREEN_HA_TOKEN", raising=False)
    monkeypatch.delenv("SMARTSCREEN_DNAKE_MQTT_USERNAME", raising=False)
    monkeypatch.delenv("SMARTSCREEN_DNAKE_MQTT_PASSWORD", raising=False)
    kwargs = dict(runtime_factory=lambda _: FakeRuntime(),
                  server_factory=lambda *args, **kw: FakeServer(),
                  device_data_file=_write_curtain_config(tmp_path))
    run_display_server(**kwargs)
    client.username_pw_set.assert_not_called()
    assert client.connect.call_count == 1
    for name in ("SMARTSCREEN_DNAKE_MQTT_USERNAME", "SMARTSCREEN_DNAKE_MQTT_PASSWORD"):
        monkeypatch.setenv(name, "test-only-value")
        with pytest.raises(ValueError, match="supplied together") as exc:
            run_display_server(**kwargs)
        assert "test-only-value" not in str(exc.value)
        assert client.connect.call_count == 1
        monkeypatch.delenv(name)


def test_application_constructs_dnake_mqtt_without_home_assistant(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        _write_curtain_config(
            tmp_path
        )
    )

    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_DNAKE_MQTT_HOST",
        "127.0.0.1",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_DNAKE_MQTT_PORT",
        "1883",
    )

    class FakeMqttClient:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            captured["client"] = self
            captured[
                "client_args"
            ] = args
            captured[
                "client_kwargs"
            ] = kwargs

    class FakeAdapter:
        def __init__(
            self,
            *,
            registry,
            ingestion,
        ):
            captured[
                "adapter"
            ] = self
            captured[
                "registry"
            ] = registry
            captured[
                "ingestion"
            ] = ingestion

    class FakeSource:
        def __init__(
            self,
            *,
            client,
            adapter,
            source_topics,
            retained_restore_topics,
            observation_accumulator,
            observation_sink,
            host,
            port,
            keepalive,
        ):
            captured[
                "source"
            ] = self
            captured[
                "source_client"
            ] = client
            captured[
                "source_adapter"
            ] = adapter
            captured[
                "source_topics"
            ] = list(
                source_topics
            )
            captured[
                "retained_restore_topics"
            ] = list(
                retained_restore_topics
            )
            captured[
                "accumulator"
            ] = (
                observation_accumulator
            )
            captured[
                "sink"
            ] = (
                observation_sink
            )
            captured[
                "host"
            ] = host
            captured[
                "port"
            ] = port
            captured[
                "keepalive"
            ] = keepalive

        def start(self):
            pass

        def stop(self):
            pass

    class FakeExecutor:
        def __init__(
            self,
            *,
            client,
            device_topics,
            device_control_topics=None,
        ):
            captured[
                "executor"
            ] = self
            captured[
                "executor_client"
            ] = client
            captured[
                "device_topics"
            ] = dict(
                device_topics
            )
            captured[
                "device_control_topics"
            ] = {
                device_id: dict(
                    topics
                )
                for (
                    device_id,
                    topics,
                )
                in (
                    device_control_topics
                    or {}
                ).items()
            }

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
                "control_registry"
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
        captured["app"] = app
        return FakeServer()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttClient",
        FakeMqttClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceControlExecutor",
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
        home_file=(
            tmp_path
            / "home.json"
        ),
    )

    assert captured[
        "source_client"
    ] is captured["client"]

    assert captured[
        "executor_client"
    ] is captured["client"]

    assert captured[
        "source_adapter"
    ] is captured["adapter"]

    assert captured[
        "source_topics"
    ] == [
        "dnake/curtain/"
        "客厅窗帘/state",
    ]

    assert captured[
        "device_topics"
    ] == {
        "living.curtain_1": (
            "dnake/curtain/"
            "客厅窗帘/set"
        ),
    }

    assert (
        captured["host"]
        == "127.0.0.1"
    )
    assert (
        captured["port"]
        == 1883
    )
    assert (
        captured["keepalive"]
        == 60
    )

    assert set(
        captured["executors"]
    ) == {
        "dnake_mqtt",
    }

    binding = (
        captured[
            "control_registry"
        ]
        .resolve(
            device_id=(
                "living.curtain_1"
            ),
            control_id="state",
        )
    )

    assert binding is not None
    assert (
        binding.adapter_id
        == "dnake_mqtt"
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


def test_application_manages_dnake_mqtt_source_lifecycle(
    monkeypatch,
    tmp_path,
):
    events = []

    device_config = (
        _write_curtain_config(
            tmp_path
        )
    )

    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    class FakeMqttClient:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            pass

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
            events.append(
                "dnake-start"
            )

        def stop(self):
            events.append(
                "dnake-stop"
            )

    class FakeExecutor:
        def __init__(
            self,
            **kwargs,
        ):
            pass

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
        "DnakeMqttClient",
        FakeMqttClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceControlExecutor",
        FakeExecutor,
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
        home_file=(
            tmp_path
            / "home.json"
        ),
    )

    assert result == 0

    assert (
        "dnake-start"
        in events
    )

    assert (
        "dnake-stop"
        in events
    )

    assert (
        events.index(
            "dnake-start"
        )
        < events.index(
            "server"
        )
    )

    assert (
        events.index(
            "dnake-stop"
        )
        < events.index(
            "server-close"
        )
    )


def _write_air_conditioner_config(
    tmp_path,
):
    path = (
        tmp_path
        / "device_data_air.json"
    )

    path.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "air_conditioner_001",
      "name": "客厅空调",
      "location_id": "living",
      "adapter_id": "dnake_mqtt",
      "adapter_config": {
        "state_topic": "dnake/air/客厅空调/state",
        "command_topics": {
          "operating_state": "dnake/air/客厅空调/mode/set",
          "target_temperature": "dnake/air/客厅空调/temp/set",
          "fan_mode": "dnake/air/客厅空调/fan/set"
        }
      },
      "parameters": {
        "operating_state": {
          "source_id": "dnake/air/客厅空调/state#operating_state",
          "value_type": "string"
        },
        "target_temperature": {
          "source_id": "dnake/air/客厅空调/state#target_temperature",
          "value_type": "float",
          "unit": "°C"
        },
        "current_temperature": {
          "source_id": "dnake/air/客厅空调/state#current_temperature",
          "value_type": "float",
          "unit": "°C"
        },
        "fan_mode": {
          "source_id": "dnake/air/客厅空调/state#fan_mode",
          "value_type": "string"
        }
      },
      "controls": {
        "operating_state": {
          "parameter": "operating_state",
          "kind": "select",
          "options": [
            "off",
            "cool",
            "heat"
          ]
        },
        "target_temperature": {
          "parameter": "target_temperature",
          "kind": "select",
          "options": [
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
            "23",
            "24",
            "25",
            "26",
            "27",
            "28",
            "29",
            "30"
          ]
        },
        "fan_mode": {
          "parameter": "fan_mode",
          "kind": "select",
          "options": [
            "low",
            "medium"
          ]
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    return path


def test_application_uses_dnake_air_state_topic_from_adapter_config(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        _write_air_conditioner_config(
            tmp_path
        )
    )

    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    class FakeMqttClient:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            captured["client"] = self

    class FakeAdapter:
        def __init__(
            self,
            *,
            registry,
            ingestion,
        ):
            pass

    class FakeSource:
        def __init__(
            self,
            *,
            client,
            adapter,
            source_topics,
            retained_restore_topics,
            observation_accumulator,
            observation_sink,
            host,
            port,
            keepalive,
        ):
            captured[
                "source_topics"
            ] = list(
                source_topics
            )
            captured[
                "retained_restore_topics"
            ] = list(
                retained_restore_topics
            )

        def start(self):
            pass

        def stop(self):
            pass

    class FakeExecutor:
        def __init__(
            self,
            *,
            client,
            device_topics,
            device_control_topics=None,
        ):
            captured[
                "device_topics"
            ] = dict(
                device_topics
            )
            captured[
                "device_control_topics"
            ] = {
                device_id: dict(
                    topics
                )
                for (
                    device_id,
                    topics,
                )
                in (
                    device_control_topics
                    or {}
                ).items()
            }

    class FakeDispatcher:
        def __init__(
            self,
            *,
            registry,
            executors,
        ):
            pass

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        return FakeServer()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttClient",
        FakeMqttClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceControlExecutor",
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
        home_file=(
            tmp_path
            / "home.json"
        ),
    )

    assert captured[
        "source_topics"
    ] == [
        "dnake/air/"
        "客厅空调/state"
    ]


def test_application_wires_dnake_control_topics_by_device_id(
    monkeypatch,
    tmp_path,
):
    captured = {}

    device_config = (
        _write_air_conditioner_config(
            tmp_path
        )
    )

    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    class FakeMqttClient:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            pass

    class FakeAdapter:
        def __init__(
            self,
            *,
            registry,
            ingestion,
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

    class FakeExecutor:
        def __init__(
            self,
            *,
            client,
            device_topics,
            device_control_topics=None,
        ):
            captured[
                "device_topics"
            ] = dict(
                device_topics
            )

            captured[
                "device_control_topics"
            ] = {
                device_id: dict(
                    topics
                )
                for (
                    device_id,
                    topics,
                )
                in (
                    device_control_topics
                    or {}
                ).items()
            }

    class FakeDispatcher:
        def __init__(
            self,
            *,
            registry,
            executors,
        ):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttClient",
        FakeMqttClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceControlExecutor",
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
            lambda *args, **kwargs:
            FakeServer()
        ),
        device_data_file=(
            device_config
        ),
        home_file=(
            tmp_path
            / "home.json"
        ),
    )

    assert captured[
        "device_topics"
    ] == {}

    assert captured[
        "device_control_topics"
    ] == {
        "air_conditioner_001": {
            "operating_state": (
                "dnake/air/"
                "客厅空调/mode/set"
            ),
            "target_temperature": (
                "dnake/air/"
                "客厅空调/temp/set"
            ),
            "fan_mode": (
                "dnake/air/"
                "客厅空调/fan/set"
            ),
        },
    }


def test_application_resolves_retained_restore_parameters_to_source_topics(
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
      "device_id": "living.light_strip_1",
      "name": "客厅灯带",
      "location_id": "living",
      "adapter_id": "dnake_mqtt",
      "parameters": {
        "power": {
          "source_id": "dnake/light/客厅灯带/state",
          "value_type": "bool"
        }
      },
      "controls": {
        "power": {
          "parameter": "power",
          "kind": "boolean"
        }
      },
      "adapter_config": {
        "command_topics": {
          "power": "dnake/light/客厅灯带/set"
        },
        "retained_restore": [
          "power"
        ]
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
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
    monkeypatch.delenv(
        "SMARTSCREEN_XINGOO_TOKEN",
        raising=False,
    )

    class FakeMqttClient:
        def __init__(
            self,
            *args,
            **kwargs,
        ):
            pass

    class FakeAdapter:
        def __init__(
            self,
            *,
            registry,
            ingestion,
        ):
            pass

    class FakeSource:
        def __init__(
            self,
            *,
            client,
            adapter,
            source_topics,
            retained_restore_topics,
            observation_accumulator,
            observation_sink,
            host,
            port,
            keepalive,
        ):
            captured[
                "source_topics"
            ] = list(
                source_topics
            )
            captured[
                "retained_restore_topics"
            ] = list(
                retained_restore_topics
            )

        def start(self):
            pass

        def stop(self):
            pass

    class FakeExecutor:
        def __init__(
            self,
            *,
            client,
            device_topics,
            device_control_topics=None,
        ):
            pass

    class FakeDispatcher:
        def __init__(
            self,
            *,
            registry,
            executors,
        ):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttClient",
        FakeMqttClient,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataAdapter",
        FakeAdapter,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceDataSource",
        FakeSource,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DnakeMqttDeviceControlExecutor",
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
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        device_data_file=device_config,
        home_file=(
            tmp_path
            / "home.json"
        ),
    )

    assert captured[
        "source_topics"
    ] == [
        "dnake/light/"
        "客厅灯带/state",
    ]

    assert captured[
        "retained_restore_topics"
    ] == [
        "dnake/light/"
        "客厅灯带/state",
    ]

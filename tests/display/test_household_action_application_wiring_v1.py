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
        pass

    def shutdown(self):
        pass

    def server_close(self):
        pass


def test_application_wires_household_action_executor(
    monkeypatch,
    tmp_path,
):
    captured = {}

    config = (
        tmp_path / "household_actions.json"
    )

    config.write_text(
        """
{
  "schema_version": 1,
  "actions": {
    "all_lights_off": [
      {
        "device_id": "kitchen.light_1",
        "control_id": "power",
        "value": false
      }
    ]
  }
}
""".strip(),
        encoding="utf-8",
    )

    class FakeHouseholdActionExecutor:
        def __init__(
            self,
            *,
            dispatcher,
            actions,
        ):
            captured["dispatcher"] = (
                dispatcher
            )
            captured["actions"] = actions

    class FakeSnapshotApplication:
        def __init__(
            self,
            host,
            **kwargs,
        ):
            captured["app_kwargs"] = kwargs

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HouseholdActionExecutor",
        FakeHouseholdActionExecutor,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "SnapshotApplication",
        FakeSnapshotApplication,
    )

    fake_dispatcher = object()

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DeviceControlDispatcher",
        lambda **kwargs: fake_dispatcher,
    )

    import json
    device_file = tmp_path / "devices.json"
    device_file.write_text(json.dumps({"schema_version": 1, "devices": [{
        "device_id": "kitchen.light_1", "name": "Demo light", "location_id": "kitchen",
        "adapter_id": "home_assistant", "adapter_config": {"entity_id": "light.demo_light"},
        "parameters": {"power": {"source_id": "light.demo_light", "value_type": "bool"}},
        "controls": {"power": {"parameter": "power", "kind": "boolean"}}
    }]}))
    monkeypatch.setenv("SMARTSCREEN_HA_URL", "http://ha.example.invalid:8123")
    monkeypatch.setenv("SMARTSCREEN_HA_TOKEN", "synthetic-test-token")
    run_display_server(
        device_data_file=device_file,
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
                FakeServer()
        ),
        household_actions_file=config,
    )

    assert captured["dispatcher"] is (
        fake_dispatcher
    )

    assert captured["actions"] == {
        "all_lights_off": (
            {
                "device_id":
                    "kitchen.light_1",
                "control_id":
                    "power",
                "value": False,
            },
        ),
    }

    assert (
        captured["app_kwargs"][
            "household_action_executor"
        ]
        is not None
    )

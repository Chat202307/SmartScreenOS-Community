import pytest

from src.smartscreen_display.application import (
    run_display_server,
)
from src.smartscreen_platform.household_state import (
    HouseholdStateEngine,
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

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


class FakeServer:
    def serve_forever(self):
        pass

    def server_close(self):
        pass


def test_application_wires_platform_pipeline_into_ha_consumer(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = tmp_path / "platform_entities.json"
    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "unit": "degC"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    provider = FakeProvider()

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["provider"] = provider
            captured["adapter"] = observation_adapter
            captured["sink"] = observation_sink

    class FakeStateStream:
        def __init__(
            self,
            *,
            base_url,
            token,
            consumer,
        ):
            captured["consumer"] = consumer

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: provider,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=lambda app, host, port, **kwargs: FakeServer(),
        platform_entities_file=platform_config,
    )

    assert captured["provider"] is provider
    assert captured["adapter"] is not None
    assert captured["sink"] is not None


def test_application_pipeline_and_dashboard_share_household_state(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = tmp_path / "platform_entities.json"
    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "unit": "degC"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["sink"] = observation_sink

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    def server_factory(app, host, port, **kwargs):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=server_factory,
        household_state_source=household_state,
        platform_entities_file=platform_config,
    )

    assert (
        captured["app"]._household_state_source
        is household_state
    )

    assert (
        captured["sink"]._household_state
        is household_state
    )


def test_application_platform_pipeline_processes_ha_observation(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = tmp_path / "platform_entities.json"
    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "unit": "degC"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = observation_adapter
            captured["sink"] = observation_sink

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=lambda app, host, port, **kwargs: FakeServer(),
        household_state_source=household_state,
        platform_entities_file=platform_config,
    )

    observations = captured["adapter"].convert(
        {
            "entity_id": "sensor.living_temperature",
            "state": "31",
            "attributes": {
                "unit_of_measurement": "°C",
            },
        }
    )

    entries = captured["sink"].process(
        observations
    )

    assert entries == []

    assert (
        household_state.get(
            "comfort",
            location_id="living",
        )
        is None
    )



def test_application_wires_observation_accumulator_into_ha_consumer(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = tmp_path / "platform_entities.json"
    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float"
    },
    {
      "entity_id": "sensor.living_humidity",
      "parameter": "humidity",
      "location_id": "living",
      "value_type": "float"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = observation_adapter
            captured["sink"] = observation_sink
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
    )

    assert captured["adapter"] is not None
    assert captured["sink"] is not None
    assert captured["accumulator"] is not None


def test_application_accumulates_temperature_and_humidity_before_pipeline(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = tmp_path / "platform_entities.json"
    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "unit": "degC"
    },
    {
      "entity_id": "sensor.living_humidity",
      "parameter": "humidity",
      "location_id": "living",
      "value_type": "float",
      "unit": "percent"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_config = (
        tmp_path / "device_data.json"
    )

    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": []
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            new_state,
        ):
            pass

    class CapturingConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            from src.smartscreen_display.home_assistant_state_events import (
                HomeAssistantStateEventConsumer,
            )

            captured["consumer"] = (
                HomeAssistantStateEventConsumer(
                    provider,
                    observation_adapter=observation_adapter,
                    observation_sink=observation_sink,
                    observation_accumulator=observation_accumulator,
                )
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        CapturingConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=household_state,
        platform_entities_file=platform_config,
        device_data_file=device_config,
    )

    consumer = captured["consumer"]

    def event(entity_id, state):
        return {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": entity_id,
                    "new_state": {
                        "entity_id": entity_id,
                        "state": state,
                        "attributes": {},
                    },
                },
            },
        }

    consumer.consume(
        event(
            "sensor.living_temperature",
            "31",
        )
    )

    consumer.consume(
        event(
            "sensor.living_humidity",
            "75",
        )
    )

    entries = household_state.snapshot()

    assert len(entries) == 1

    entry = entries[0]

    assert entry["location_id"] == "living"

    assert (
        entry["value"]["dimensions"]["thermal"]
        == "hot"
    )

    assert (
        entry["value"]["dimensions"]["humidity"]
        == "high"
    )


def test_application_wires_parameter_freshness_policy_into_accumulator(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "max_age_seconds": 300
    },
    {
      "entity_id": "binary_sensor.living_presence",
      "parameter": "presence",
      "location_id": "living",
      "value_type": "bool",
      "max_age_seconds": 60
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
    )

    accumulator = captured["accumulator"]

    assert accumulator is not None

    assert accumulator._max_age_by_parameter == {}

    assert (
        accumulator._max_age_by_location_parameter[
            ("living", "temperature")
        ]
        == 300
    )
    assert (
        accumulator._max_age_by_location_parameter[
            ("living", "presence")
        ]
        == 60
    )


def test_application_ignores_entities_without_freshness_policy(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "max_age_seconds": 300
    },
    {
      "entity_id": "sensor.living_humidity",
      "parameter": "humidity",
      "location_id": "living",
      "value_type": "float"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
    )

    accumulator = captured["accumulator"]

    assert accumulator._max_age_by_parameter == {}

    assert (
        accumulator._max_age_by_location_parameter[
            ("living", "temperature")
        ]
        == 300
    )
    assert (
        ("living", "humidity")
        not in
        accumulator._max_age_by_location_parameter
    )


def test_application_wires_location_parameter_freshness_policy(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "binary_sensor.living_presence",
      "parameter": "presence",
      "location_id": "living",
      "value_type": "bool",
      "max_age_seconds": 60
    },
    {
      "entity_id": "binary_sensor.bedroom_presence",
      "parameter": "presence",
      "location_id": "bedroom",
      "value_type": "bool",
      "max_age_seconds": 120
    },
    {
      "entity_id": "sensor.living_temperature",
      "parameter": "temperature",
      "location_id": "living",
      "value_type": "float",
      "max_age_seconds": 300
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": []
}
""".strip(),
        encoding="utf-8",
    )


    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
        device_data_file=device_data_config,
    )

    accumulator = captured["accumulator"]

    assert accumulator is not None

    assert (
        accumulator._max_age_by_location_parameter[
            ("living", "presence")
        ]
        == 60
    )
    assert (
        accumulator._max_age_by_location_parameter[
            ("bedroom", "presence")
        ]
        == 120
    )
    assert (
        accumulator._max_age_by_location_parameter[
            ("living", "temperature")
        ]
        == 300
    )


def test_application_location_freshness_overrides_parameter_fallback(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "binary_sensor.living_presence",
      "parameter": "presence",
      "location_id": "living",
      "value_type": "bool",
      "max_age_seconds": 60
    },
    {
      "entity_id": "binary_sensor.bedroom_presence",
      "parameter": "presence",
      "location_id": "bedroom",
      "value_type": "bool",
      "max_age_seconds": 120
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
    )

    accumulator = captured["accumulator"]

    # Location-scoped policies must remain location-scoped.
    # They must not create a parameter-wide fallback.
    assert (
        "presence"
        not in accumulator._max_age_by_parameter
    )

    # Location-specific policy must remain precise.
    assert accumulator._max_age_for(
        "living",
        "presence",
    ) == 60

    assert accumulator._max_age_for(
        "bedroom",
        "presence",
    ) == 120


def test_application_wires_presence_occupancy_pipeline(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "binary_sensor.living_presence",
      "parameter": "presence",
      "location_id": "living",
      "value_type": "bool",
      "max_age_seconds": 60
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["sink"] = observation_sink

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=platform_config,
    )

    pipeline = captured["sink"]

    assert pipeline is not None

    interpreter_types = {
        type(interpreter).__name__
        for interpreter in pipeline._interpreters
    }

    capability_names = {
        capability.name
        for capability in pipeline._capabilities
    }

    assert "PresenceInterpreter" in interpreter_types
    assert "occupancy" in capability_names


def test_application_presence_observation_produces_occupancy_state(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "binary_sensor.living_presence",
      "parameter": "presence",
      "location_id": "living",
      "value_type": "bool",
      "max_age_seconds": 60
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = (
                observation_adapter
            )
            captured["sink"] = (
                observation_sink
            )
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=household_state,
        platform_entities_file=platform_config,
    )

    observations = captured["adapter"].convert(
        {
            "entity_id": "binary_sensor.living_presence",
            "state": "on",
            "attributes": {},
        }
    )

    current = captured["accumulator"].update(
        observations
    )

    entries = captured["sink"].process(
        current
    )

    assert len(entries) == 1

    entry = household_state.get(
        "occupancy",
        location_id="living",
    )

    assert entry is not None
    assert entry.target == "occupancy"
    assert entry.location_id == "living"
    assert entry.source_capability == "occupancy"

    assert entry.value == {
        "state": "occupied",
        "count": None,
    }


def test_application_presence_off_produces_unoccupied_state(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "binary_sensor.living_presence",
      "parameter": "presence",
      "location_id": "living",
      "value_type": "bool",
      "max_age_seconds": 60
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = (
                observation_adapter
            )
            captured["sink"] = (
                observation_sink
            )
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=household_state,
        platform_entities_file=platform_config,
    )

    observations = captured["adapter"].convert(
        {
            "entity_id": "binary_sensor.living_presence",
            "state": "off",
            "attributes": {},
        }
    )

    current = captured["accumulator"].update(
        observations
    )

    entries = captured["sink"].process(
        current
    )

    assert len(entries) == 1

    entry = household_state.get(
        "occupancy",
        location_id="living",
    )

    assert entry is not None
    assert entry.target == "occupancy"
    assert entry.location_id == "living"
    assert entry.source_capability == "occupancy"

    assert entry.value == {
        "state": "unoccupied",
        "count": 0,
    }


def test_application_wires_freshness_sweep(
    monkeypatch,
):
    captured = {}

    class FakeProvider:
        pass

    class FakeSweep:
        def __init__(
            self,
            *,
            accumulator,
            observation_sink,
            interval_seconds=5.0,
        ):
            captured["accumulator"] = accumulator
            captured["sink"] = observation_sink
            captured["interval_seconds"] = (
                interval_seconds
            )
            captured["sweep"] = self

        def start(self):
            captured["started"] = True

        def stop(self):
            captured["stopped"] = True

        def join(self, timeout=None):
            captured["join_timeout"] = timeout

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationFreshnessSweep",
        FakeSweep,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    result = run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=lambda app, host, port, **kwargs: FakeServer(),
    )

    assert result is None
    assert captured["accumulator"] is not None
    assert captured["sink"] is not None
    assert captured["started"] is True
    assert captured["stopped"] is True
    assert captured["join_timeout"] == 5.0


def test_application_wires_weather_advice_capability(
    monkeypatch,
):
    captured = {}

    class FakeProvider:
        pass

    class FakeWeatherAdviceCapability:
        pass

    class FakePipeline:
        def __init__(
            self,
            *,
            household_state,
            interpreters,
            capabilities,
            knowledge=None,
        ):
            captured["capabilities"] = list(
                capabilities
            )

        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "WeatherAdviceCapability",
        FakeWeatherAdviceCapability,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "PlatformStatePipeline",
        FakePipeline,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=lambda app, host, port, **kwargs: FakeServer(),
    )

    assert any(
        isinstance(
            capability,
            FakeWeatherAdviceCapability,
        )
        for capability in captured[
            "capabilities"
        ]
    )


def test_application_weather_observations_produce_advice(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.outdoor_rain_probability",
      "parameter": "precipitation_probability",
      "location_id": "outdoor",
      "value_type": "float",
      "unit": "percent"
    },
    {
      "entity_id": "sensor.demo_entity_046",
      "parameter": "apparent_temperature",
      "location_id": "outdoor",
      "value_type": "float",
      "unit": "degC"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = (
                observation_adapter
            )
            captured["sink"] = (
                observation_sink
            )
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=(
            household_state
        ),
        platform_entities_file=(
            platform_config
        ),
    )

    rain = captured[
        "adapter"
    ].convert(
        {
            "entity_id": (
                "sensor.outdoor_rain_probability"
            ),
            "state": "80",
            "attributes": {
                "unit_of_measurement": "%",
            },
        }
    )

    apparent = captured[
        "adapter"
    ].convert(
        {
            "entity_id": (
                "sensor.demo_entity_046"
            ),
            "state": "7",
            "attributes": {
                "unit_of_measurement": "°C",
            },
        }
    )

    accumulated = captured[
        "accumulator"
    ].update(rain)

    captured["sink"].process(
        accumulated,
        location_id="outdoor",
    )

    accumulated = captured[
        "accumulator"
    ].update(apparent)

    captured["sink"].process(
        accumulated,
        location_id="outdoor",
    )

    umbrella = household_state.get(
        "umbrella_advice",
        location_id="outdoor",
    )

    clothing = household_state.get(
        "clothing_advice",
        location_id="outdoor",
    )

    assert umbrella is not None
    assert (
        umbrella.value["recommended"]
        is True
    )

    assert clothing is not None
    assert (
        clothing.value["level"]
        == "warm"
    )


def test_application_weather_advice_is_location_scoped(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.garden_rain_probability",
      "parameter": "precipitation_probability",
      "location_id": "garden",
      "value_type": "float",
      "unit": "percent"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = (
                observation_adapter
            )
            captured["sink"] = (
                observation_sink
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=(
            household_state
        ),
        platform_entities_file=(
            platform_config
        ),
    )

    observations = captured[
        "adapter"
    ].convert(
        {
            "entity_id": (
                "sensor.garden_rain_probability"
            ),
            "state": "90",
            "attributes": {
                "unit_of_measurement": "%",
            },
        }
    )

    entries = captured[
        "sink"
    ].process(
        observations,
        location_id="garden",
    )

    assert len(entries) == 1
    assert (
        entries[0].target
        == "umbrella_advice"
    )
    assert (
        entries[0].location_id
        == "garden"
    )


def test_application_wires_configured_motion_idle_policy_to_occupancy(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_motion_idle",
      "parameter": "motion_idle_seconds",
      "location_id": "corridor",
      "value_type": "int",
      "unit": "s"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    occupancy_config = (
        tmp_path
        / "occupancy_interpretation.json"
    )

    occupancy_config.write_text(
        """
{
  "schema_version": 1,
  "sources": [
    {
      "entity_id": "sensor.corridor_motion_idle",
      "location_id": "corridor",
      "parameter": "motion_idle_seconds",
      "strategy": "motion_idle_threshold",
      "settings": {
        "occupied_below_seconds": 60
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = (
                observation_adapter
            )
            captured["sink"] = (
                observation_sink
            )
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    class FakeWeatherSource:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantWeatherForecastSource",
        FakeWeatherSource,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=(
            household_state
        ),
        platform_entities_file=(
            platform_config
        ),
        occupancy_interpretation_file=(
            occupancy_config
        ),
    )

    observations = captured[
        "adapter"
    ].convert(
        {
            "entity_id":
                "sensor.corridor_motion_idle",
            "state": "0",
            "attributes": {
                "unit_of_measurement": "s",
            },
        }
    )

    assert len(observations) == 1
    assert (
        observations[0].parameter
        == "motion_idle_seconds"
    )

    accumulated = captured[
        "accumulator"
    ].update(
        observations
    )

    captured["sink"].process(
        accumulated,
        location_id="corridor",
    )

    occupancy = household_state.get(
        "occupancy",
        location_id="corridor",
    )

    assert occupancy is not None
    assert occupancy.location_id == "corridor"
    assert occupancy.value == {
        "state": "occupied",
        "count": None,
    }


def test_application_wires_illuminance_interpreter(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["sink"] = observation_sink

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
    )

    interpreter_types = {
        type(interpreter).__name__
        for interpreter
        in captured["sink"]._interpreters
    }

    assert "ThermalInterpreter" in interpreter_types
    assert "IlluminanceInterpreter" in interpreter_types
    assert "PresenceInterpreter" in interpreter_types


def test_application_wires_lighting_capability(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["sink"] = observation_sink

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
    )

    capability_names = [
        capability.name
        for capability
        in captured["sink"]._capabilities
    ]

    assert "lighting" in capability_names


def test_application_illuminance_observation_produces_lighting_state(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = observation_adapter
            captured["sink"] = observation_sink
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=(
            household_state
        ),
        platform_entities_file=(
            platform_config
        ),
    )

    observations = captured[
        "adapter"
    ].convert(
        {
            "entity_id":
                "sensor.corridor_illuminance",
            "state": "45",
            "attributes": {
                "unit_of_measurement": "lx",
            },
        }
    )

    accumulated = captured[
        "accumulator"
    ].update(
        observations
    )

    captured[
        "sink"
    ].process(
        accumulated,
        location_id="corridor",
    )

    lighting = household_state.get(
        "lighting",
        location_id="corridor",
    )

    assert lighting is not None
    assert lighting.target == "lighting"
    assert lighting.location_id == "corridor"
    assert lighting.value == {
        "state": "dim",
    }

    assert (
        observations[0].observation_id
        in lighting.evidence_refs
    )


def test_application_uses_configured_lighting_thresholds(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    lighting_config = (
        tmp_path
        / "lighting_interpretation.json"
    )

    lighting_config.write_text(
        """
{
  "schema_version": 1,
  "defaults": {
    "dim_below_lux": 80,
    "bright_above_lux": 1200
  },
  "locations": {
    "corridor": {
      "dim_below_lux": 50,
      "bright_above_lux": 500
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    household_state = HouseholdStateEngine()

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            captured["adapter"] = (
                observation_adapter
            )
            captured["sink"] = (
                observation_sink
            )
            captured["accumulator"] = (
                observation_accumulator
            )

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        household_state_source=(
            household_state
        ),
        platform_entities_file=(
            platform_config
        ),
        lighting_interpretation_file=(
            lighting_config
        ),
    )

    observations = captured[
        "adapter"
    ].convert(
        {
            "entity_id":
                "sensor.corridor_illuminance",
            "state": "60",
            "attributes": {
                "unit_of_measurement": "lx",
            },
        }
    )

    accumulated = captured[
        "accumulator"
    ].update(
        observations
    )

    captured[
        "sink"
    ].process(
        accumulated,
        location_id="corridor",
    )

    lighting = household_state.get(
        "lighting",
        location_id="corridor",
    )

    assert lighting is not None

    assert lighting.value == {
        "state": "comfortable",
    }


def test_application_wires_device_data_adapter(
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
      "device_id": "corridor.motion_sensor_1",
      "name": "过廊人体",
      "location_id": "corridor",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.corridor_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
            **kwargs,
        ):
            captured["device_data_adapter"] = (
                device_data_adapter
            )

    class FakeStateStream:
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

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_config
        ),
    )

    adapter = captured[
        "device_data_adapter"
    ]

    assert adapter is not None

    binding = (
        adapter._registry.resolve_source(
            adapter_id="home_assistant",
            source_id=(
                "sensor."
                "corridor_illuminance"
            ),
        )
    )

    assert binding is not None
    assert binding.device_id == (
        "corridor.motion_sensor_1"
    )
    assert binding.parameter == (
        "illuminance"
    )


def test_application_device_data_side_write_updates_store(
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
      "device_id": "corridor.motion_sensor_1",
      "name": "过廊人体",
      "location_id": "corridor",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.corridor_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            device_data_adapter=None,
            **kwargs,
        ):
            captured["adapter"] = (
                device_data_adapter
            )

    class FakeStateStream:
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

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_config
        ),
    )

    adapter = captured["adapter"]

    observation = adapter.ingest_state(
        entity_id="sensor.corridor_illuminance",
        raw_state="45",
    )

    assert observation.value == 45.0

    entry = adapter._ingestion._store.get(
        "corridor.motion_sensor_1",
        "illuminance",
    )

    assert entry is not None
    assert entry.value == 45.0
    assert entry.unit == "lux"


def test_application_device_data_primary_path_does_not_require_platform_entity_mapping(
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
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": []
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
            **kwargs,
        ):
            captured[
                "observation_adapter"
            ] = observation_adapter

            captured[
                "observation_sink"
            ] = observation_sink

            captured[
                "observation_accumulator"
            ] = observation_accumulator

            captured[
                "device_data_adapter"
            ] = device_data_adapter

    class FakeStateStream:
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

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_config
        ),
    )

    assert (
        captured[
            "device_data_adapter"
        ]
        is not None
    )

    assert (
        captured[
            "observation_sink"
        ]
        is not None
    )

    assert (
        captured[
            "observation_accumulator"
        ]
        is not None
    )

    assert (
        captured[
            "observation_adapter"
        ]
        is not None
    )

    assert (
        captured[
            "observation_adapter"
        ]._entities
        == {}
    )


def test_application_uses_device_data_freshness_for_mapped_parameters(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_illuminance",
      "parameter": "illuminance",
      "location_id": "living",
      "value_type": "float",
      "unit": "lux",
      "max_age_seconds": 999
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path
        / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux",
          "max_age_seconds": 60
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_seconds=None,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            clock=None,
        ):
            captured[
                "max_age_by_parameter"
            ] = dict(
                max_age_by_parameter or {}
            )

            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

        def snapshot(self):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
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

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_data_config
        ),
    )

    assert captured[
        "max_age_by_location_parameter"
    ][
        (
            "living",
            "illuminance",
        )
    ] == 60


def test_application_does_not_inherit_legacy_freshness_for_migrated_device_parameter_without_max_age(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_illuminance",
      "parameter": "illuminance",
      "location_id": "living",
      "value_type": "float",
      "unit": "lux",
      "max_age_seconds": 999
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path
        / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_seconds=None,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            clock=None,
        ):
            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

        def snapshot(self):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
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

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_data_config
        ),
    )

    assert (
        (
            "living",
            "illuminance",
        )
        not in captured[
            "max_age_by_location_parameter"
        ]
    )


def test_application_freshness_ownership_is_source_scoped_not_parameter_scoped(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_illuminance",
      "parameter": "illuminance",
      "location_id": "living",
      "value_type": "float",
      "unit": "lux",
      "max_age_seconds": 999
    },
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux",
      "max_age_seconds": 300
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path
        / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_seconds=None,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            clock=None,
        ):
            captured[
                "max_age_by_parameter"
            ] = dict(
                max_age_by_parameter or {}
            )

            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

        def snapshot(self):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
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

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_data_config
        ),
    )

    policies = captured[
        "max_age_by_location_parameter"
    ]

    assert (
        "living",
        "illuminance",
    ) not in policies

    assert policies[
        (
            "corridor",
            "illuminance",
        )
    ] == 300


def test_application_legacy_parameter_fallback_does_not_leak_into_canonical_source(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.living_illuminance",
      "parameter": "illuminance",
      "location_id": "living",
      "value_type": "float",
      "unit": "lux",
      "max_age_seconds": 999
    },
    {
      "entity_id": "sensor.corridor_illuminance",
      "parameter": "illuminance",
      "location_id": "corridor",
      "value_type": "float",
      "unit": "lux",
      "max_age_seconds": 300
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "living.sensor_1",
      "name": "客厅传感器",
      "location_id": "living",
      "adapter_id": "home_assistant",
      "parameters": {
        "illuminance": {
          "source_id": "sensor.living_illuminance",
          "value_type": "float",
          "unit": "lux"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_seconds=None,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            clock=None,
        ):
            captured["max_age_seconds"] = (
                max_age_seconds
            )
            captured["max_age_by_parameter"] = dict(
                max_age_by_parameter or {}
            )
            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

        def snapshot(self):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_data_config
        ),
    )

    # The legacy corridor source owns a
    # location-specific 300 second policy.
    assert captured[
        "max_age_by_location_parameter"
    ][
        ("corridor", "illuminance")
    ] == 300

    # It must NOT become a parameter-wide
    # fallback, because that would also expire
    # canonical living/illuminance even though
    # Device Data deliberately has no policy.
    assert (
        "illuminance"
        not in captured[
            "max_age_by_parameter"
        ]
    )

    assert captured[
        "max_age_seconds"
    ] is None


def test_application_keeps_parameter_fallback_for_unscoped_legacy_freshness(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": [
    {
      "entity_id": "sensor.generic_temperature",
      "parameter": "temperature",
      "value_type": "float",
      "unit": "degC",
      "max_age_seconds": 300
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": []
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_seconds=None,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            clock=None,
        ):
            captured["max_age_seconds"] = (
                max_age_seconds
            )
            captured["max_age_by_parameter"] = dict(
                max_age_by_parameter or {}
            )
            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

        def snapshot(self):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
        def __init__(self, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def join(self, timeout=None):
            pass

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_data_config
        ),
    )

    assert captured[
        "max_age_by_parameter"
    ] == {
        "temperature": 300,
    }

    assert (
        "temperature"
        in captured[
            "max_age_by_parameter"
        ]
    )
    assert (
        ("living", "temperature")
        not in captured[
            "max_age_by_location_parameter"
        ]
    )

    assert captured[
        "max_age_seconds"
    ] is None


def test_application_uses_parameter_observation_location_for_device_data_freshness(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )

    platform_config.write_text(
        """
{
  "entities": []
}
""".strip(),
        encoding="utf-8",
    )

    device_data_config = (
        tmp_path
        / "device_data.json"
    )

    device_data_config.write_text(
        """
{
  "schema_version": 1,
  "devices": [
    {
      "device_id": "kitchen.sensor_1",
      "name": "厨房人体",
      "location_id": "kitchen",
      "adapter_id": "home_assistant",
      "parameters": {
        "presence": {
          "source_id": "binary_sensor.kitchen_presence",
          "value_type": "bool",
          "max_age_seconds": 60,
          "observation_location_id": "open_public_area"
        },
        "illuminance": {
          "source_id": "sensor.kitchen_lux",
          "value_type": "float",
          "unit": "lux",
          "max_age_seconds": 120
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeProvider:
        pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_seconds=None,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            clock=None,
        ):
            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

        def snapshot(self):
            return []

    class FakeConsumer:
        def __init__(
            self,
            provider,
            *,
            observation_adapter=None,
            observation_sink=None,
            observation_accumulator=None,
            device_data_adapter=None,
        ):
            pass

    class FakeStateStream:
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

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "create_home_assistant_provider",
        lambda **kwargs: FakeProvider(),
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateEventConsumer",
        FakeConsumer,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "HomeAssistantStateStream",
        FakeStateStream,
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    run_display_server(
        runtime_factory=(
            lambda path: FakeRuntime()
        ),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=(
            device_data_config
        ),
    )

    policies = captured[
        "max_age_by_location_parameter"
    ]

    assert policies[
        (
            "open_public_area",
            "presence",
        )
    ] == 60

    assert policies[
        (
            "kitchen",
            "illuminance",
        )
    ] == 120

    assert (
        "kitchen",
        "presence",
    ) not in policies

    assert (
        "open_public_area",
        "illuminance",
    ) not in policies


def test_application_wires_device_power_dependency_resolver_into_dashboard(
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
      "device_id": "dining.light_power_1",
      "name": "餐灯",
      "location_id": "dining",
      "adapter_id": "home_assistant",
      "parameters": {
        "power": {
          "source_id": "light.dining_power",
          "value_type": "bool"
        }
      }
    },
    {
      "device_id": "dining.table_light_east",
      "name": "餐桌灯东",
      "location_id": "dining",
      "adapter_id": "home_assistant",
      "power_source_device_id": "dining.light_power_1",
      "parameters": {
        "power": {
          "source_id": "light.table_light_east",
          "value_type": "bool"
        }
      }
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    class FakeResolver:
        def __init__(
            self,
            *,
            registry,
            store,
        ):
            captured["resolver_registry"] = (
                registry
            )
            captured["resolver_store"] = (
                store
            )
            captured["resolver"] = self

        def resolve(
            self,
            *,
            device_id,
            parameter,
        ):
            return "unavailable"

    class FakeStore:
        def __init__(
            self,
            *,
            registry,
        ):
            captured["store_registry"] = (
                registry
            )
            captured["store"] = self

        def get(
            self,
            device_id,
            parameter,
        ):
            return None

        def update_source(
            self,
            **kwargs,
        ):
            return None

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DeviceParameterStore",
        FakeStore,
    )

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "DevicePowerDependencyResolver",
        FakeResolver,
        raising=False,
    )

    def server_factory(
        app,
        host,
        port,
        **kwargs,
    ):
        captured["app"] = app
        return FakeServer()

    run_display_server(
        runtime_factory=(
            lambda path:
            FakeRuntime()
        ),
        server_factory=server_factory,
        device_data_file=(
            device_config
        ),
    )

    assert (
        captured[
            "resolver_registry"
        ]
        is captured[
            "store_registry"
        ]
    )

    assert (
        captured[
            "resolver_store"
        ]
        is captured[
            "store"
        ]
    )

    assert (
        captured[
            "app"
        ]
        ._device_power_dependency_resolver
        is captured[
            "resolver"
        ]
    )


def test_application_wires_canonical_weather_freshness_policy(
    monkeypatch,
    tmp_path,
):
    captured = {}

    platform_config = (
        tmp_path
        / "platform_entities.json"
    )
    platform_config.write_text(
        """
{
  "entities": []
}
""".strip(),
        encoding="utf-8",
    )

    device_config = (
        tmp_path
        / "device_data.json"
    )
    device_config.write_text(
        """
{
  "schema_version": 1,
  "devices": []
}
""".strip(),
        encoding="utf-8",
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

        def server_close(self):
            pass

    class FakeAccumulator:
        def __init__(
            self,
            *,
            max_age_by_parameter=None,
            max_age_by_location_parameter=None,
            **kwargs,
        ):
            captured[
                "max_age_by_parameter"
            ] = dict(
                max_age_by_parameter or {}
            )
            captured[
                "max_age_by_location_parameter"
            ] = dict(
                max_age_by_location_parameter
                or {}
            )

        def locations(self):
            return []

    monkeypatch.setattr(
        "src.smartscreen_display.application."
        "ObservationAccumulator",
        FakeAccumulator,
    )

    from src.smartscreen_display.application import (
        run_display_server,
    )

    run_display_server(
        runtime_factory=lambda path: FakeRuntime(),
        server_factory=(
            lambda app, host, port, **kwargs:
            FakeServer()
        ),
        platform_entities_file=(
            platform_config
        ),
        device_data_file=device_config,
        home_file=tmp_path / "home.json",
    )

    policy = captured[
        "max_age_by_location_parameter"
    ]

    assert policy[
        ("outdoor", "weather_condition")
    ] == 3600
    assert policy[
        ("outdoor", "temperature")
    ] == 3600
    assert policy[
        ("outdoor", "humidity")
    ] == 3600
    assert policy[
        ("outdoor", "apparent_temperature")
    ] == 3600
    assert policy[
        ("outdoor", "wind_speed")
    ] == 3600
    assert policy[
        (
            "outdoor",
            "forecast_precipitation",
        )
    ] == 3600
    assert policy[
        ("outdoor", "forecast_condition")
    ] == 3600

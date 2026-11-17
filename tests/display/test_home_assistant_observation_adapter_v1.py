from src.smartscreen_display.home_assistant_observations import (
    HomeAssistantObservationAdapter,
)


def test_adapter_converts_temperature_sensor():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.living_temperature",
                "parameter": "temperature",
                "location_id": "living",
                "value_type": "float",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.living_temperature",
            "state": "26.5",
            "attributes": {
                "device_class": "temperature",
                "unit_of_measurement": "°C",
            },
        }
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.parameter == "temperature"
    assert observation.value == 26.5
    assert observation.unit == "°C"
    assert observation.location_id == "living"
    assert observation.confidence == 1.0

    assert observation.provenance == {
        "provider": "home_assistant",
        "entity_id": "sensor.living_temperature",
    }


def test_adapter_converts_humidity_sensor():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.living_humidity",
                "parameter": "humidity",
                "location_id": "living",
                "value_type": "float",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.living_humidity",
            "state": "58",
            "attributes": {
                "device_class": "humidity",
                "unit_of_measurement": "%",
            },
        }
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.parameter == "humidity"
    assert observation.value == 58.0
    assert observation.unit == "%"
    assert observation.location_id == "living"


def test_adapter_converts_binary_presence_sensor():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "binary_sensor.living_presence",
                "parameter": "presence",
                "location_id": "living",
                "value_type": "bool",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "binary_sensor.living_presence",
            "state": "on",
            "attributes": {
                "device_class": "occupancy",
            },
        }
    )

    assert len(observations) == 1
    assert observations[0].parameter == "presence"
    assert observations[0].value is True
    assert observations[0].location_id == "living"


def test_adapter_converts_binary_off_to_false():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "binary_sensor.living_presence",
                "parameter": "presence",
                "location_id": "living",
                "value_type": "bool",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "binary_sensor.living_presence",
            "state": "off",
            "attributes": {},
        }
    )

    assert observations[0].value is False


def test_adapter_ignores_unconfigured_entity():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.living_temperature",
                "parameter": "temperature",
                "location_id": "living",
                "value_type": "float",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.bedroom_temperature",
            "state": "23",
            "attributes": {},
        }
    )

    assert observations == []


def test_adapter_ignores_unavailable_state():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.living_temperature",
                "parameter": "temperature",
                "location_id": "living",
                "value_type": "float",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.living_temperature",
            "state": "unavailable",
            "attributes": {},
        }
    )

    assert observations == []


def test_adapter_ignores_unknown_state():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.living_temperature",
                "parameter": "temperature",
                "location_id": "living",
                "value_type": "float",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.living_temperature",
            "state": "unknown",
            "attributes": {},
        }
    )

    assert observations == []


def test_adapter_ignores_invalid_numeric_value():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.living_temperature",
                "parameter": "temperature",
                "location_id": "living",
                "value_type": "float",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.living_temperature",
            "state": "not-a-number",
            "attributes": {},
        }
    )

    assert observations == []


def test_adapter_converts_motion_idle_seconds_sensor():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.corridor_motion_idle",
                "parameter": "motion_idle_seconds",
                "location_id": "corridor",
                "value_type": "int",
                "unit": "s",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.corridor_motion_idle",
            "state": "60",
            "attributes": {
                "unit_of_measurement": "s",
            },
        }
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.parameter == "motion_idle_seconds"
    assert observation.value == 60
    assert observation.unit == "s"
    assert observation.location_id == "corridor"


def test_adapter_converts_corridor_illuminance_sensor():
    adapter = HomeAssistantObservationAdapter(
        entities=[
            {
                "entity_id": "sensor.corridor_illuminance",
                "parameter": "illuminance",
                "location_id": "corridor",
                "value_type": "float",
                "unit": "lux",
            }
        ]
    )

    observations = adapter.convert(
        {
            "entity_id": "sensor.corridor_illuminance",
            "state": "14",
            "attributes": {
                "unit_of_measurement": "lx",
            },
        }
    )

    assert len(observations) == 1

    observation = observations[0]

    assert observation.parameter == "illuminance"
    assert observation.value == 14.0
    assert observation.unit == "lux"
    assert observation.location_id == "corridor"

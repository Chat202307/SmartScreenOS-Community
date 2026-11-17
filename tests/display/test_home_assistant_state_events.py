from src.smartscreen_display.home_assistant_state_events import (
    HomeAssistantStateEventConsumer,
)


class FakeProvider:
    def __init__(self):
        self.updates = []

    def update_state(
        self,
        entity_id,
        new_state,
    ):
        self.updates.append(
            (
                entity_id,
                new_state,
            )
        )


def test_state_event_consumer_updates_provider():
    provider = FakeProvider()

    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    new_state = {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {},
    }

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": "light.living_room",
                    "new_state": new_state,
                },
            },
        }
    )

    assert provider.updates == [
        (
            "light.living_room",
            new_state,
        )
    ]


def test_state_event_consumer_handles_removed_entity():
    provider = FakeProvider()

    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": "light.living_room",
                    "new_state": None,
                },
            },
        }
    )

    assert provider.updates == [
        (
            "light.living_room",
            None,
        )
    ]


def test_state_event_consumer_ignores_non_state_events():
    provider = FakeProvider()

    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "call_service",
                "data": {},
            },
        }
    )

    assert provider.updates == []


def test_state_event_consumer_ignores_non_event_messages():
    provider = FakeProvider()

    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "id": 1,
            "type": "result",
            "success": True,
            "result": None,
        }
    )

    assert provider.updates == []


def test_state_event_consumer_ignores_missing_event():
    provider = FakeProvider()
    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "type": "event",
        }
    )

    assert provider.updates == []


def test_state_event_consumer_ignores_invalid_event_data():
    provider = FakeProvider()
    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": "invalid",
            },
        }
    )

    assert provider.updates == []


def test_state_event_consumer_ignores_missing_entity_id():
    provider = FakeProvider()
    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "new_state": None,
                },
            },
        }
    )

    assert provider.updates == []


def test_state_event_consumer_ignores_invalid_new_state():
    provider = FakeProvider()
    consumer = HomeAssistantStateEventConsumer(
        provider
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id":
                        "light.living_room",
                    "new_state": "invalid",
                },
            },
        }
    )

    assert provider.updates == []


class FakeObservationAdapter:
    def __init__(self):
        self.states = []

    def convert(self, state):
        self.states.append(state)
        return ["observation-1"]


class FakeObservationSink:
    def __init__(self):
        self.received = []

    def process(self, observations):
        self.received.append(
            list(observations)
        )


def test_state_event_consumer_forwards_observations_to_sink():
    provider = FakeProvider()
    adapter = FakeObservationAdapter()
    sink = FakeObservationSink()

    consumer = HomeAssistantStateEventConsumer(
        provider,
        observation_adapter=adapter,
        observation_sink=sink,
    )

    new_state = {
        "entity_id": "sensor.living_temperature",
        "state": "26.5",
        "attributes": {
            "unit_of_measurement": "°C",
        },
    }

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id":
                        "sensor.living_temperature",
                    "new_state": new_state,
                },
            },
        }
    )

    assert provider.updates == [
        (
            "sensor.living_temperature",
            new_state,
        )
    ]

    assert adapter.states == [
        new_state,
    ]

    assert sink.received == [
        ["observation-1"],
    ]


def test_state_event_consumer_does_not_call_sink_for_unmapped_state():
    provider = FakeProvider()

    class EmptyAdapter:
        def convert(self, state):
            return []

    sink = FakeObservationSink()

    consumer = HomeAssistantStateEventConsumer(
        provider,
        observation_adapter=EmptyAdapter(),
        observation_sink=sink,
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": "light.unmapped",
                    "new_state": {
                        "entity_id": "light.unmapped",
                        "state": "on",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert sink.received == []


def test_state_event_consumer_does_not_forward_removed_entity():
    provider = FakeProvider()
    adapter = FakeObservationAdapter()
    sink = FakeObservationSink()

    consumer = HomeAssistantStateEventConsumer(
        provider,
        observation_adapter=adapter,
        observation_sink=sink,
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id":
                        "sensor.living_temperature",
                    "new_state": None,
                },
            },
        }
    )

    assert provider.updates == [
        (
            "sensor.living_temperature",
            None,
        )
    ]

    assert adapter.states == []
    assert sink.received == []


def test_state_event_consumer_accumulates_observations_before_sink():
    from src.smartscreen_platform.contracts import Observation
    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )

    provider = FakeProvider()
    accumulator = ObservationAccumulator()

    class Adapter:
        def convert(self, state):
            parameter = state["entity_id"].split(".")[-1]

            return [
                Observation.create(
                    parameter=parameter,
                    value=float(state["state"]),
                    location_id="living",
                )
            ]

    class Sink:
        def __init__(self):
            self.received = []

        def process(self, observations):
            self.received.append(
                list(observations)
            )

    sink = Sink()

    consumer = HomeAssistantStateEventConsumer(
        provider,
        observation_adapter=Adapter(),
        observation_sink=sink,
        observation_accumulator=accumulator,
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": "sensor.temperature",
                    "new_state": {
                        "entity_id": "sensor.temperature",
                        "state": "31",
                        "attributes": {},
                    },
                },
            },
        }
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": "sensor.humidity",
                    "new_state": {
                        "entity_id": "sensor.humidity",
                        "state": "75",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert len(sink.received) == 2

    assert [
        item.parameter
        for item in sink.received[0]
    ] == [
        "temperature",
    ]

    assert [
        item.parameter
        for item in sink.received[1]
    ] == [
        "temperature",
        "humidity",
    ]

    assert [
        item.value
        for item in sink.received[1]
    ] == [
        31.0,
        75.0,
    ]


def test_state_event_consumer_without_accumulator_preserves_existing_behavior():
    from src.smartscreen_platform.contracts import Observation

    provider = FakeProvider()

    class Adapter:
        def convert(self, state):
            return [
                Observation.create(
                    parameter="temperature",
                    value=31.0,
                    location_id="living",
                )
            ]

    class Sink:
        def __init__(self):
            self.received = []

        def process(self, observations):
            self.received.append(
                list(observations)
            )

    sink = Sink()

    consumer = HomeAssistantStateEventConsumer(
        provider,
        observation_adapter=Adapter(),
        observation_sink=sink,
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": "sensor.temperature",
                    "new_state": {
                        "entity_id": "sensor.temperature",
                        "state": "31",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert len(sink.received) == 1
    assert len(sink.received[0]) == 1
    assert sink.received[0][0].parameter == "temperature"


def test_observation_sink_receives_location_context():
    class Provider:
        def update_state(self, entity_id, new_state):
            pass

    class Adapter:
        def convert(self, new_state):
            from src.smartscreen_platform.contracts import (
                Observation,
            )

            return [
                Observation.create(
                    "presence",
                    True,
                    location_id="living",
                )
            ]

    class Sink:
        def __init__(self):
            self.calls = []

        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            self.calls.append(
                (
                    list(observations),
                    location_id,
                )
            )

    sink = Sink()

    consumer = HomeAssistantStateEventConsumer(
        Provider(),
        observation_adapter=Adapter(),
        observation_sink=sink,
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "binary_sensor.living_presence"
                    ),
                    "new_state": {
                        "entity_id": (
                            "binary_sensor.living_presence"
                        ),
                        "state": "on",
                    },
                },
            },
        }
    )

    assert len(sink.calls) == 1
    assert sink.calls[0][1] == "living"


def test_observation_sink_keeps_location_when_accumulator_returns_empty():
    class Provider:
        def update_state(self, entity_id, new_state):
            pass

    class Adapter:
        def convert(self, new_state):
            from src.smartscreen_platform.contracts import (
                Observation,
            )

            return [
                Observation.create(
                    "presence",
                    True,
                    location_id="living",
                )
            ]

    class Accumulator:
        def update(self, observations):
            return []

    class Sink:
        def __init__(self):
            self.calls = []

        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            self.calls.append(
                (
                    list(observations),
                    location_id,
                )
            )

    sink = Sink()

    consumer = HomeAssistantStateEventConsumer(
        Provider(),
        observation_adapter=Adapter(),
        observation_sink=sink,
        observation_accumulator=Accumulator(),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "binary_sensor.living_presence"
                    ),
                    "new_state": {
                        "entity_id": (
                            "binary_sensor.living_presence"
                        ),
                        "state": "on",
                    },
                },
            },
        }
    )

    assert sink.calls == [
        (
            [],
            "living",
        )
    ]


def test_state_event_consumer_can_write_device_data_ingestion():
    captured = {}

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            captured["provider"] = (
                entity_id,
                state,
            )

    class FakeIngestion:
        def ingest(
            self,
            *,
            adapter_id,
            source_id,
            value,
            available=True,
        ):
            captured["ingestion"] = {
                "adapter_id": adapter_id,
                "source_id": source_id,
                "value": value,
                "available": available,
            }

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        device_data_ingestion=FakeIngestion(),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": "49",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "ingestion"
    ] == {
        "adapter_id": "home_assistant",
        "source_id": (
            "sensor."
            "living_illuminance"
        ),
        "value": "49",
        "available": True,
    }


def test_state_event_consumer_marks_unavailable_device_data():
    captured = {}

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeIngestion:
        def ingest(
            self,
            *,
            adapter_id,
            source_id,
            value,
            available=True,
        ):
            captured["ingestion"] = {
                "value": value,
                "available": available,
            }

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        device_data_ingestion=FakeIngestion(),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": "unavailable",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "ingestion"
    ] == {
        "value": "unavailable",
        "available": False,
    }


def test_state_event_consumer_ignores_unknown_device_data_source():
    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeIngestion:
        def ingest(
            self,
            *,
            adapter_id,
            source_id,
            value,
            available=True,
        ):
            raise ValueError(
                "unknown adapter/source"
            )

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        device_data_ingestion=FakeIngestion(),
    )

    # Device Data is a migration side path.
    # An unmapped source must not break the
    # existing Home Assistant event path.
    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "sensor.unmapped"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor.unmapped"
                        ),
                        "state": "123",
                        "attributes": {},
                    },
                },
            },
        }
    )


def test_state_event_consumer_can_write_device_data_adapter():
    captured = {}

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            captured["device_data"] = {
                "entity_id": entity_id,
                "raw_state": raw_state,
            }

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": "49",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured["device_data"] == {
        "entity_id": (
            "sensor."
            "living_illuminance"
        ),
        "raw_state": {
            "entity_id": (
                "sensor."
                "living_illuminance"
            ),
            "state": "49",
            "attributes": {},
        },
    }


def test_state_event_consumer_passes_unavailable_to_device_data_adapter():
    captured = {}

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            captured["raw_state"] = (
                raw_state
            )

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": "unavailable",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured["raw_state"] == {
        "entity_id": (
            "sensor."
            "living_illuminance"
        ),
        "state": "unavailable",
        "attributes": {},
    }


def test_state_event_consumer_prefers_device_data_observation_for_mapped_source():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {
        "legacy_calls": 0,
    }

    device_observation = Observation.create(
        parameter="illuminance",
        value=49.0,
        unit="lux",
        location_id="living",
        provenance={
            "provider": "home_assistant",
            "adapter_id": "home_assistant",
            "device_id": (
                "living.presence_sensor_1"
            ),
            "source_id": (
                "sensor.living_illuminance"
            ),
        },
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            captured[
                "device_data_call"
            ] = {
                "entity_id": entity_id,
                "raw_state": raw_state,
            }

            return device_observation

    class FakeLegacyObservationAdapter:
        def convert(
            self,
            state,
        ):
            captured["legacy_calls"] += 1

            return [
                Observation.create(
                    parameter="illuminance",
                    value=999.0,
                    unit="lux",
                    location_id="living",
                )
            ]

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            captured[
                "accumulator"
            ] = list(observations)

            return list(observations)

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = (
                list(observations)
            )
            captured[
                "location_id"
            ] = location_id

            return []

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_adapter=(
            FakeLegacyObservationAdapter()
        ),
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": "49",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "device_data_call"
    ] == {
        "entity_id": (
            "sensor.living_illuminance"
        ),
        "raw_state": {
            "entity_id": (
                "sensor."
                "living_illuminance"
            ),
            "state": "49",
            "attributes": {},
        },
    }

    assert captured["legacy_calls"] == 0

    assert captured[
        "accumulator"
    ] == [
        device_observation
    ]

    assert captured[
        "sink"
    ] == [
        device_observation
    ]

    assert (
        captured["location_id"]
        == "living"
    )


def test_state_event_consumer_falls_back_to_legacy_observation_for_unmapped_device_source():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {
        "legacy_calls": 0,
    }

    legacy_observation = Observation.create(
        parameter="temperature",
        value=24.0,
        unit="degC",
        location_id="living",
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            captured[
                "device_data_called"
            ] = True

            return None

    class FakeLegacyObservationAdapter:
        def convert(
            self,
            state,
        ):
            captured["legacy_calls"] += 1
            return [
                legacy_observation
            ]

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            return list(
                observations
            )

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = (
                list(observations)
            )
            return []

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_adapter=(
            FakeLegacyObservationAdapter()
        ),
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "sensor."
                        "legacy_temperature"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "legacy_temperature"
                        ),
                        "state": "24",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "device_data_called"
    ] is True

    assert captured["legacy_calls"] == 1

    assert captured[
        "sink"
    ] == [
        legacy_observation
    ]


def test_state_event_consumer_withdraws_mapped_unavailable_device_observation():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {}

    unavailable = Observation.create(
        parameter="illuminance",
        value="unavailable",
        unit="lux",
        quality="unavailable",
        location_id="living",
        provenance={
            "provider": "home_assistant",
            "adapter_id": "home_assistant",
            "device_id": (
                "living.presence_sensor_1"
            ),
            "source_id": (
                "sensor.living_illuminance"
            ),
        },
    )

    remaining_presence = Observation.create(
        parameter="presence",
        value=True,
        location_id="living",
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            return unavailable

    class FakeLegacyObservationAdapter:
        def convert(
            self,
            state,
        ):
            raise AssertionError(
                "legacy adapter must not be used"
            )

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            raise AssertionError(
                "unavailable observation must "
                "not be accumulated"
            )

        def withdraw(
            self,
            location_id,
            parameter,
        ):
            captured["withdraw"] = (
                location_id,
                parameter,
            )

            return [
                remaining_presence
            ]

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = list(
                observations
            )
            captured["location_id"] = (
                location_id
            )
            return []

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_adapter=(
            FakeLegacyObservationAdapter()
        ),
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": (
                            "unavailable"
                        ),
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "withdraw"
    ] == (
        "living",
        "illuminance",
    )

    assert captured[
        "sink"
    ] == [
        remaining_presence
    ]

    assert (
        captured["location_id"]
        == "living"
    )


def test_state_event_consumer_processes_empty_location_after_last_unavailable_device_observation():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {}

    unavailable = Observation.create(
        parameter="presence",
        value="unavailable",
        quality="unavailable",
        location_id="living",
        provenance={
            "provider": "home_assistant",
            "adapter_id": "home_assistant",
            "device_id": (
                "living.presence_sensor_1"
            ),
            "source_id": (
                "binary_sensor."
                "living_presence"
            ),
        },
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            return unavailable

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            raise AssertionError(
                "unavailable observation must "
                "not be accumulated"
            )

        def withdraw(
            self,
            location_id,
            parameter,
        ):
            captured["withdraw"] = (
                location_id,
                parameter,
            )
            return []

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = list(
                observations
            )
            captured["location_id"] = (
                location_id
            )
            return []

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_adapter=None,
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "binary_sensor."
                        "living_presence"
                    ),
                    "new_state": {
                        "entity_id": (
                            "binary_sensor."
                            "living_presence"
                        ),
                        "state": (
                            "unavailable"
                        ),
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "withdraw"
    ] == (
        "living",
        "presence",
    )

    assert captured[
        "sink"
    ] == []

    assert (
        captured["location_id"]
        == "living"
    )


def test_mapped_device_presence_unavailable_withdraws_household_occupancy():
    from src.smartscreen_display.home_assistant_device_data import (
        HomeAssistantDeviceDataAdapter,
    )
    from src.smartscreen_platform.capabilities.occupancy import (
        OccupancyCapability,
    )
    from src.smartscreen_platform.device_data import (
        DeviceDataIngestionService,
        DeviceDefinition,
        DeviceParameterDefinition,
        DeviceParameterStore,
        DeviceRegistry,
    )
    from src.smartscreen_platform.household_state import (
        HouseholdStateEngine,
    )
    from src.smartscreen_platform.interpretation import (
        PresenceInterpreter,
    )
    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )
    from src.smartscreen_platform.state_pipeline import (
        PlatformStatePipeline,
    )

    registry = DeviceRegistry(
        devices=[
            DeviceDefinition(
                device_id=(
                    "living.presence_sensor_1"
                ),
                name="客厅人体",
                location_id="living",
                adapter_id="home_assistant",
                parameters={
                    "presence": (
                        DeviceParameterDefinition(
                            parameter="presence",
                            source_id=(
                                "binary_sensor."
                                "living_presence"
                            ),
                            value_type="bool",
                        )
                    ),
                },
            )
        ]
    )

    store = DeviceParameterStore(
        registry=registry
    )

    ingestion = DeviceDataIngestionService(
        registry=registry,
        store=store,
    )

    device_data_adapter = (
        HomeAssistantDeviceDataAdapter(
            registry=registry,
            ingestion=ingestion,
        )
    )

    accumulator = ObservationAccumulator()

    household_state = HouseholdStateEngine()

    pipeline = PlatformStatePipeline(
        household_state=household_state,
        interpreters=[
            PresenceInterpreter(),
        ],
        capabilities=[
            OccupancyCapability(),
        ],
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_adapter=None,
        observation_sink=pipeline,
        observation_accumulator=(
            accumulator
        ),
        device_data_adapter=(
            device_data_adapter
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "binary_sensor."
                        "living_presence"
                    ),
                    "new_state": {
                        "entity_id": (
                            "binary_sensor."
                            "living_presence"
                        ),
                        "state": "on",
                        "attributes": {},
                    },
                },
            },
        }
    )

    occupied = household_state.get(
        "occupancy",
        location_id="living",
    )

    assert occupied is not None
    assert occupied.value == {
        "state": "occupied",
        "count": None,
    }

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "binary_sensor."
                        "living_presence"
                    ),
                    "new_state": {
                        "entity_id": (
                            "binary_sensor."
                            "living_presence"
                        ),
                        "state": (
                            "unavailable"
                        ),
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert accumulator.for_location(
        "living"
    ) == []

    assert (
        household_state.get(
            "occupancy",
            location_id="living",
        )
        is None
    )


def test_state_event_consumer_mapped_device_data_does_not_require_legacy_observation_adapter():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {}

    device_observation = Observation.create(
        parameter="illuminance",
        value=49.0,
        unit="lux",
        location_id="living",
        provenance={
            "provider": "home_assistant",
            "adapter_id": "home_assistant",
            "device_id": (
                "living.presence_sensor_1"
            ),
            "source_id": (
                "sensor.living_illuminance"
            ),
        },
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            captured[
                "device_data_call"
            ] = {
                "entity_id": entity_id,
                "raw_state": raw_state,
            }

            return device_observation

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            captured[
                "accumulator"
            ] = list(
                observations
            )

            return list(
                observations
            )

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = list(
                observations
            )
            captured[
                "location_id"
            ] = location_id

            return []

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_adapter=None,
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": (
                    "state_changed"
                ),
                "data": {
                    "entity_id": (
                        "sensor."
                        "living_illuminance"
                    ),
                    "new_state": {
                        "entity_id": (
                            "sensor."
                            "living_illuminance"
                        ),
                        "state": "49",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured[
        "device_data_call"
    ] == {
        "entity_id": (
            "sensor.living_illuminance"
        ),
        "raw_state": {
            "entity_id": (
                "sensor."
                "living_illuminance"
            ),
            "state": "49",
            "attributes": {},
        },
    }

    assert captured[
        "accumulator"
    ] == [
        device_observation
    ]

    assert captured[
        "sink"
    ] == [
        device_observation
    ]

    assert (
        captured["location_id"]
        == "living"
    )


def test_state_event_consumer_passes_full_state_to_device_data_adapter():
    captured = {}

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            captured["entity_id"] = entity_id
            captured["raw_state"] = raw_state
            return None

    new_state = {
        "entity_id": "light.smart_light",
        "state": "on",
        "attributes": {
            "brightness": 128,
            "color_temp_kelvin": 4000,
        },
    }

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "light.smart_light"
                    ),
                    "new_state": new_state,
                },
            },
        }
    )

    assert captured["entity_id"] == (
        "light.smart_light"
    )
    assert captured["raw_state"] == new_state


def test_state_event_consumer_accepts_device_data_observation_batch():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {}

    power = Observation.create(
        parameter="power",
        value=True,
        location_id="living",
    )

    brightness = Observation.create(
        parameter="brightness",
        value=50,
        unit="percent",
        location_id="living",
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            return [
                power,
                brightness,
            ]

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            captured["accumulator"] = list(
                observations
            )
            return list(observations)

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = list(
                observations
            )
            captured["location_id"] = (
                location_id
            )

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "light.smart_light"
                    ),
                    "new_state": {
                        "entity_id": (
                            "light.smart_light"
                        ),
                        "state": "on",
                        "attributes": {
                            "brightness": 128,
                        },
                    },
                },
            },
        }
    )

    assert captured["accumulator"] == [
        power,
        brightness,
    ]

    assert captured["sink"] == [
        power,
        brightness,
    ]

    assert captured["location_id"] == (
        "living"
    )


def test_state_event_consumer_withdraws_all_unavailable_observations_in_batch():
    from src.smartscreen_platform.contracts import (
        Observation,
    )

    captured = {
        "withdraws": [],
    }

    unavailable_power = Observation.create(
        parameter="power",
        value=None,
        quality="unavailable",
        location_id="living",
    )

    unavailable_brightness = Observation.create(
        parameter="brightness",
        value=None,
        unit="percent",
        quality="unavailable",
        location_id="living",
    )

    unavailable_color_temperature = (
        Observation.create(
            parameter="color_temperature",
            value=None,
            unit="K",
            quality="unavailable",
            location_id="living",
        )
    )

    remaining = Observation.create(
        parameter="presence",
        value=True,
        location_id="living",
    )

    class FakeProvider:
        def update_state(
            self,
            entity_id,
            state,
        ):
            pass

    class FakeDeviceDataAdapter:
        def ingest_state(
            self,
            *,
            entity_id,
            raw_state,
        ):
            return [
                unavailable_power,
                unavailable_brightness,
                unavailable_color_temperature,
            ]

    class FakeAccumulator:
        def update(
            self,
            observations,
        ):
            raise AssertionError(
                "unavailable observations "
                "must not be accumulated"
            )

        def withdraw(
            self,
            location_id,
            parameter,
        ):
            captured["withdraws"].append(
                (
                    location_id,
                    parameter,
                )
            )

            return [remaining]

    class FakeSink:
        def process(
            self,
            observations,
            *,
            location_id=None,
        ):
            captured["sink"] = list(
                observations
            )
            captured["location_id"] = (
                location_id
            )

    consumer = HomeAssistantStateEventConsumer(
        FakeProvider(),
        observation_sink=FakeSink(),
        observation_accumulator=(
            FakeAccumulator()
        ),
        device_data_adapter=(
            FakeDeviceDataAdapter()
        ),
    )

    consumer.consume(
        {
            "type": "event",
            "event": {
                "event_type": "state_changed",
                "data": {
                    "entity_id": (
                        "light.smart_light"
                    ),
                    "new_state": {
                        "entity_id": (
                            "light.smart_light"
                        ),
                        "state": "unavailable",
                        "attributes": {},
                    },
                },
            },
        }
    )

    assert captured["withdraws"] == [
        (
            "living",
            "power",
        ),
        (
            "living",
            "brightness",
        ),
        (
            "living",
            "color_temperature",
        ),
    ]

    assert captured["sink"] == [
        remaining
    ]

    assert captured["location_id"] == (
        "living"
    )

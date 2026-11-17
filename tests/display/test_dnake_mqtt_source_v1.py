from types import SimpleNamespace

from src.smartscreen_display.dnake_mqtt_source import (
    DnakeMqttDeviceDataSource,
)


class FakeAdapter:
    def __init__(self):
        self.calls = []

    def ingest_message(
        self,
        *,
        topic,
        raw_payload,
    ):
        self.calls.append(
            (
                topic,
                raw_payload,
            )
        )

        return SimpleNamespace(
            location_id="living",
            parameter="state",
            quality="good",
        )


class FakeAccumulator:
    def __init__(self):
        self.updated = []

    def update(self, observations):
        self.updated.extend(
            observations
        )

    def for_location(
        self,
        location_id,
    ):
        return list(self.updated)


class FakeSink:
    def __init__(self):
        self.processed = []

    def process(
        self,
        observations,
        *,
        location_id,
    ):
        self.processed.append(
            (
                location_id,
                list(observations),
            )
        )


class FakeMqttClient:
    def __init__(self):
        self.on_connect = None
        self.on_message = None
        self.subscriptions = []

    def subscribe(self, topic):
        self.subscriptions.append(topic)


def test_subscribes_only_declared_state_topics():
    client = FakeMqttClient()

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=FakeAdapter(),
        source_topics=[
            "dnake/curtain/"
            "客厅窗帘/state",
        ],
    )

    source._on_connect(
        client,
        None,
        None,
        0,
        None,
    )

    assert client.subscriptions == [
        "dnake/curtain/"
        "客厅窗帘/state",
    ]


def test_message_enters_observation_pipeline():
    client = FakeMqttClient()
    adapter = FakeAdapter()
    accumulator = FakeAccumulator()
    sink = FakeSink()

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=adapter,
        source_topics=[
            "dnake/curtain/"
            "客厅窗帘/state",
        ],
        observation_accumulator=(
            accumulator
        ),
        observation_sink=sink,
    )

    message = SimpleNamespace(
        topic=(
            "dnake/curtain/"
            "客厅窗帘/state"
        ),
        payload="OPEN".encode(
            "utf-8"
        ),
    )

    source._on_message(
        client,
        None,
        message,
    )

    assert adapter.calls == [
        (
            "dnake/curtain/"
            "客厅窗帘/state",
            "OPEN",
        ),
    ]

    assert len(
        accumulator.updated
    ) == 1

    assert sink.processed[0][0] == "living"


class FakeLifecycleMqttClient:
    def __init__(self):
        self.on_connect = None
        self.on_message = None
        self.calls = []

    def connect(
        self,
        host,
        port,
        keepalive,
    ):
        self.calls.append(
            (
                "connect",
                host,
                port,
                keepalive,
            )
        )

    def loop_start(self):
        self.calls.append(
            ("loop_start",)
        )

    def disconnect(self):
        self.calls.append(
            ("disconnect",)
        )

    def loop_stop(self):
        self.calls.append(
            ("loop_stop",)
        )


def test_start_connects_and_starts_mqtt_loop():
    client = FakeLifecycleMqttClient()

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=FakeAdapter(),
        source_topics=[
            "dnake/curtain/"
            "客厅窗帘/state",
        ],
        host="127.0.0.1",
        port=1883,
        keepalive=60,
    )

    source.start()

    assert client.calls == [
        (
            "connect",
            "127.0.0.1",
            1883,
            60,
        ),
        ("loop_start",),
    ]


def test_stop_disconnects_and_stops_mqtt_loop():
    client = FakeLifecycleMqttClient()

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=FakeAdapter(),
        source_topics=[],
    )

    source.start()
    client.calls.clear()

    source.stop()

    assert client.calls == [
        ("disconnect",),
        ("loop_stop",),
    ]


def test_retained_state_is_not_ingested_as_fresh_observation():
    calls = []

    class RetainedAdapter:
        def ingest_message(
            self,
            *,
            topic,
            raw_payload,
        ):
            calls.append(
                (
                    topic,
                    raw_payload,
                )
            )

            raise AssertionError(
                "retained MQTT state must not "
                "be ingested as a fresh observation"
            )

    class RetainedMessage:
        topic = (
            "dnake/curtain/"
            "客厅窗帘/state"
        )
        payload = b"STOPPED"
        retain = True

    class FakeClient:
        pass

    client = FakeClient()

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=RetainedAdapter(),
        source_topics=[
            "dnake/curtain/"
            "客厅窗帘/state",
        ],
    )

    source._on_message(
        client,
        None,
        RetainedMessage(),
    )

    assert calls == []


def test_multiple_observations_enter_pipeline_as_batch():
    client = FakeMqttClient()
    accumulator = FakeAccumulator()
    sink = FakeSink()

    observations = [
        SimpleNamespace(
            location_id="living",
            parameter="operating_state",
            quality="good",
        ),
        SimpleNamespace(
            location_id="living",
            parameter="target_temperature",
            quality="good",
        ),
        SimpleNamespace(
            location_id="living",
            parameter="current_temperature",
            quality="good",
        ),
        SimpleNamespace(
            location_id="living",
            parameter="fan_mode",
            quality="good",
        ),
    ]

    class BatchAdapter:
        def ingest_message(
            self,
            *,
            topic,
            raw_payload,
        ):
            return observations

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=BatchAdapter(),
        source_topics=[
            "dnake/air/"
            "客厅空调/state",
        ],
        observation_accumulator=(
            accumulator
        ),
        observation_sink=sink,
    )

    message = SimpleNamespace(
        topic=(
            "dnake/air/"
            "客厅空调/state"
        ),
        payload=b'{"power":"ON"}',
        retain=False,
    )

    source._on_message(
        client,
        None,
        message,
    )

    assert accumulator.updated == (
        observations
    )

    assert len(sink.processed) == 1

    assert (
        sink.processed[0][0]
        == "living"
    )

    assert (
        sink.processed[0][1]
        == observations
    )


def test_single_observation_source_behavior_remains_supported():
    client = FakeMqttClient()
    adapter = FakeAdapter()
    accumulator = FakeAccumulator()
    sink = FakeSink()

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=adapter,
        source_topics=[
            "dnake/curtain/"
            "客厅窗帘/state",
        ],
        observation_accumulator=(
            accumulator
        ),
        observation_sink=sink,
    )

    message = SimpleNamespace(
        topic=(
            "dnake/curtain/"
            "客厅窗帘/state"
        ),
        payload=b"OPEN",
        retain=False,
    )

    source._on_message(
        client,
        None,
        message,
    )

    assert len(
        accumulator.updated
    ) == 1

    assert len(
        sink.processed
    ) == 1


def test_unavailable_fan_withdraws_previous_fan_from_accumulator():
    from src.smartscreen_platform.observation_accumulator import (
        ObservationAccumulator,
    )

    client = FakeMqttClient()
    accumulator = ObservationAccumulator()
    sink = FakeSink()

    batches = [
        [
            SimpleNamespace(
                location_id="living",
                parameter="operating_state",
                quality="good",
                value="cool",
            ),
            SimpleNamespace(
                location_id="living",
                parameter="fan_mode",
                quality="good",
                value="low",
            ),
        ],
        [
            SimpleNamespace(
                location_id="living",
                parameter="operating_state",
                quality="good",
                value="off",
            ),
            SimpleNamespace(
                location_id="living",
                parameter="fan_mode",
                quality="unavailable",
                value=None,
            ),
        ],
    ]

    class SequencedAdapter:
        def ingest_message(
            self,
            *,
            topic,
            raw_payload,
        ):
            return batches.pop(0)

    source = DnakeMqttDeviceDataSource(
        client=client,
        adapter=SequencedAdapter(),
        source_topics=[
            "dnake/air/客厅空调/state",
        ],
        observation_accumulator=(
            accumulator
        ),
        observation_sink=sink,
    )

    message = SimpleNamespace(
        topic="dnake/air/客厅空调/state",
        payload=b'{"state":1}',
        retain=False,
    )

    source._on_message(
        client,
        None,
        message,
    )

    first_parameters = {
        observation.parameter
        for observation
        in accumulator.for_location(
            "living"
        )
    }

    assert first_parameters == {
        "operating_state",
        "fan_mode",
    }

    source._on_message(
        client,
        None,
        message,
    )

    current = accumulator.for_location(
        "living"
    )

    assert {
        observation.parameter
        for observation in current
    } == {
        "operating_state",
    }

    operating_state = next(
        observation
        for observation in current
        if observation.parameter
        == "operating_state"
    )

    assert operating_state.value == "off"

    latest_sink_observations = (
        sink.processed[-1][1]
    )

    assert {
        observation.parameter
        for observation
        in latest_sink_observations
    } == {
        "operating_state",
    }


def test_allowed_retained_state_restores_without_entering_observation_pipeline():
    class RestoreAdapter:
        def __init__(self):
            self.ingested = []
            self.restored = []

        def ingest_message(
            self,
            *,
            topic,
            raw_payload,
        ):
            self.ingested.append(
                (topic, raw_payload)
            )
            raise AssertionError(
                "retained state must not "
                "enter fresh ingestion"
            )

        def restore_message(
            self,
            *,
            topic,
            raw_payload,
        ):
            self.restored.append(
                (topic, raw_payload)
            )
            return SimpleNamespace(
                device_id="living.light_strip_1",
                parameter="power",
                value=False,
                updated_at="",
            )

    class RetainedMessage:
        topic = (
            "dnake/light/"
            "客厅灯带/state"
        )
        payload = b"OFF"
        retain = True

    adapter = RestoreAdapter()
    accumulator = FakeAccumulator()
    sink = FakeSink()

    source = DnakeMqttDeviceDataSource(
        client=FakeMqttClient(),
        adapter=adapter,
        source_topics=[
            "dnake/light/"
            "客厅灯带/state",
        ],
        retained_restore_topics=[
            "dnake/light/"
            "客厅灯带/state",
        ],
        observation_accumulator=(
            accumulator
        ),
        observation_sink=sink,
    )

    source._on_message(
        source._client,
        None,
        RetainedMessage(),
    )

    assert adapter.restored == [
        (
            "dnake/light/"
            "客厅灯带/state",
            "OFF",
        ),
    ]
    assert adapter.ingested == []
    assert accumulator.updated == []
    assert sink.processed == []

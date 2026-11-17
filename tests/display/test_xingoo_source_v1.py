from types import SimpleNamespace

from src.smartscreen_display.xingoo_source import (
    XingooDeviceDataSource,
)


class FakeClient:
    def __init__(
        self,
        properties_by_iot_id,
    ):
        self._properties_by_iot_id = (
            properties_by_iot_id
        )
        self.calls = []

    def get_all_properties(
        self,
        *,
        iot_id,
    ):
        self.calls.append(
            iot_id
        )

        return (
            self._properties_by_iot_id[
                iot_id
            ]
        )


class FakeAdapter:
    def __init__(
        self,
        *,
        location_by_iot_id=None,
        quality_by_iot_id=None,
    ):
        self.calls = []
        self._location_by_iot_id = (
            location_by_iot_id or {}
        )
        self._quality_by_iot_id = (
            quality_by_iot_id or {}
        )

    def ingest_properties(
        self,
        *,
        iot_id,
        properties,
    ):
        self.calls.append(
            (
                iot_id,
                properties,
            )
        )

        return [
            SimpleNamespace(
                location_id=(
                    self._location_by_iot_id.get(
                        iot_id,
                        "living",
                    )
                ),
                parameter="pm25",
                value=properties.get(
                    "PM25"
                ),
                quality=(
                    self._quality_by_iot_id.get(
                        iot_id,
                        "good",
                    )
                ),
            )
        ]


class FakeAccumulator:
    def __init__(self):
        self.current = {}
        self.update_calls = []
        self.withdraw_calls = []
        self.for_location_calls = []

    def update(
        self,
        observations,
    ):
        observations = list(
            observations
        )

        self.update_calls.append(
            observations
        )

        if not observations:
            return []

        location_id = (
            observations[0].location_id
        )

        current = self.current.setdefault(
            location_id,
            {},
        )

        for observation in observations:
            current[
                observation.parameter
            ] = observation

        return list(
            current.values()
        )

    def withdraw(
        self,
        location_id,
        parameter,
    ):
        self.withdraw_calls.append(
            (
                location_id,
                parameter,
            )
        )

        current = self.current.setdefault(
            location_id,
            {},
        )

        current.pop(
            parameter,
            None,
        )

        return list(
            current.values()
        )

    def for_location(
        self,
        location_id,
    ):
        self.for_location_calls.append(
            location_id
        )

        return list(
            self.current.get(
                location_id,
                {},
            ).values()
        )


class FakeSink:
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


def test_source_fetches_and_adapts_properties():
    client = FakeClient(
        {
            "iot-1": {
                "PM25": 33,
            }
        }
    )

    adapter = FakeAdapter()

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
        ],
    )

    result = source.refresh()

    assert client.calls == [
        "iot-1"
    ]

    assert adapter.calls == [
        (
            "iot-1",
            {
                "PM25": 33,
            },
        )
    ]

    assert len(result) == 1
    assert result[0].value == 33


def test_source_supports_multiple_devices():
    client = FakeClient(
        {
            "iot-1": {
                "PM25": 33,
            },
            "iot-2": {
                "PM25": 18,
            },
        }
    )

    adapter = FakeAdapter(
        location_by_iot_id={
            "iot-1": "living",
            "iot-2": "bedroom",
        }
    )

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
            "iot-2",
        ],
    )

    result = source.refresh()

    assert client.calls == [
        "iot-1",
        "iot-2",
    ]

    assert len(result) == 2


def test_source_updates_accumulator_per_location():
    client = FakeClient(
        {
            "iot-1": {
                "PM25": 33,
            },
            "iot-2": {
                "PM25": 18,
            },
        }
    )

    adapter = FakeAdapter(
        location_by_iot_id={
            "iot-1": "living",
            "iot-2": "bedroom",
        }
    )

    accumulator = FakeAccumulator()

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
            "iot-2",
        ],
        observation_accumulator=(
            accumulator
        ),
    )

    result = source.refresh()

    assert len(
        accumulator.update_calls
    ) == 2

    assert {
        call[0].location_id
        for call
        in accumulator.update_calls
    } == {
        "living",
        "bedroom",
    }

    assert len(result) == 2


def test_source_sends_each_location_to_pipeline():
    client = FakeClient(
        {
            "iot-1": {
                "PM25": 33,
            },
            "iot-2": {
                "PM25": 18,
            },
        }
    )

    adapter = FakeAdapter(
        location_by_iot_id={
            "iot-1": "living",
            "iot-2": "bedroom",
        }
    )

    sink = FakeSink()

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
            "iot-2",
        ],
        observation_sink=sink,
    )

    source.refresh()

    assert len(
        sink.calls
    ) == 2

    assert {
        location_id
        for _, location_id
        in sink.calls
    } == {
        "living",
        "bedroom",
    }


def test_source_withdraws_unavailable_observation():
    client = FakeClient(
        {
            "iot-1": {
                "PM25": "unavailable",
            }
        }
    )

    adapter = FakeAdapter(
        quality_by_iot_id={
            "iot-1": "unavailable",
        }
    )

    accumulator = FakeAccumulator()

    previous = SimpleNamespace(
        location_id="living",
        parameter="pm25",
        value=33,
        quality="good",
    )

    accumulator.update(
        [
            previous
        ]
    )

    accumulator.update_calls.clear()

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
        ],
        observation_accumulator=(
            accumulator
        ),
    )

    result = source.refresh()

    assert (
        accumulator.withdraw_calls
        == [
            (
                "living",
                "pm25",
            )
        ]
    )

    assert (
        accumulator.update_calls
        == []
    )

    assert result == []


def test_source_notifies_pipeline_when_last_observation_is_withdrawn():
    client = FakeClient(
        {
            "iot-1": {
                "PM25": "unavailable",
            }
        }
    )

    adapter = FakeAdapter(
        quality_by_iot_id={
            "iot-1": "unavailable",
        }
    )

    accumulator = FakeAccumulator()

    accumulator.update(
        [
            SimpleNamespace(
                location_id="living",
                parameter="pm25",
                value=33,
                quality="good",
            )
        ]
    )

    sink = FakeSink()

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
        ],
        observation_accumulator=(
            accumulator
        ),
        observation_sink=sink,
    )

    result = source.refresh()

    assert result == []

    assert sink.calls == [
        (
            [],
            "living",
        )
    ]


def test_source_does_not_call_sink_for_empty_observations():
    class EmptyAdapter:
        def ingest_properties(
            self,
            *,
            iot_id,
            properties,
        ):
            return []

    sink = FakeSink()

    source = XingooDeviceDataSource(
        client=FakeClient(
            {
                "iot-1": {
                    "Unknown": 1,
                }
            }
        ),
        adapter=EmptyAdapter(),
        iot_ids=[
            "iot-1",
        ],
        observation_sink=sink,
    )

    assert (
        source.refresh()
        == []
    )

    assert sink.calls == []


def test_source_background_lifecycle():
    import time

    client = FakeClient(
        {
            "iot-1": {
                "PM25": 33,
            }
        }
    )

    adapter = FakeAdapter()

    source = XingooDeviceDataSource(
        client=client,
        adapter=adapter,
        iot_ids=[
            "iot-1",
        ],
        poll_interval_seconds=60.0,
        retry_interval_seconds=0.01,
    )

    assert source.is_alive() is False

    source.start()

    deadline = (
        time.monotonic()
        + 1.0
    )

    while (
        not client.calls
        and time.monotonic()
        < deadline
    ):
        time.sleep(0.01)

    assert client.calls == [
        "iot-1"
    ]

    assert source.is_alive() is True

    source.stop()
    source.join(
        timeout=1.0
    )

    assert source.is_alive() is False


def test_source_start_is_idempotent():
    import time

    client = FakeClient(
        {
            "iot-1": {
                "PM25": 33,
            }
        }
    )

    source = XingooDeviceDataSource(
        client=client,
        adapter=FakeAdapter(),
        iot_ids=[
            "iot-1",
        ],
        poll_interval_seconds=60.0,
    )

    source.start()

    first_thread = source._thread

    source.start()

    assert source._thread is first_thread

    source.stop()
    source.join(
        timeout=1.0
    )


def test_source_background_retries_after_refresh_error():
    from threading import Event

    recovered = Event()

    class RecoveringClient:
        def __init__(self):
            self.calls = 0

        def get_all_properties(
            self,
            *,
            iot_id,
        ):
            self.calls += 1

            if self.calls == 1:
                raise RuntimeError(
                    "temporary failure"
                )

            recovered.set()
            return {
                "PM25": 33,
            }

    client = RecoveringClient()

    source = XingooDeviceDataSource(
        client=client,
        adapter=FakeAdapter(),
        iot_ids=[
            "iot-1",
        ],
        poll_interval_seconds=60.0,
        retry_interval_seconds=0.01,
    )

    source.start()
    try:
        # Synchronize on recovery, not unsynchronized one-second polling.
        # Keep a finite watchdog and clean up even when the assertion fails.
        assert recovered.wait(timeout=10.0), "source did not retry after refresh failure"
    finally:
        source.stop()
        source.join(timeout=5.0)

    assert client.calls >= 2
    assert source.is_alive() is False

from __future__ import annotations


class DnakeMqttDeviceDataSource:
    def __init__(
        self,
        *,
        client,
        adapter,
        source_topics,
        retained_restore_topics=None,
        observation_accumulator=None,
        observation_sink=None,
        host="127.0.0.1",
        port=1883,
        keepalive=60,
    ):
        self._client = client
        self._adapter = adapter
        self._source_topics = list(
            source_topics or []
        )
        self._retained_restore_topics = set(
            retained_restore_topics or []
        )
        self._observation_accumulator = (
            observation_accumulator
        )
        self._observation_sink = (
            observation_sink
        )
        self._host = str(host)
        self._port = int(port)
        self._keepalive = int(
            keepalive
        )
        self._started = False

        self._client.on_connect = (
            self._on_connect
        )
        self._client.on_message = (
            self._on_message
        )

    def start(self):
        if self._started:
            return

        self._client.connect(
            self._host,
            self._port,
            self._keepalive,
        )
        self._client.loop_start()
        self._started = True

    def stop(self):
        if not self._started:
            return

        self._client.disconnect()
        self._client.loop_stop()
        self._started = False

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties=None,
    ):
        for topic in self._source_topics:
            client.subscribe(topic)

    def _on_message(
        self,
        client,
        userdata,
        message,
    ):
        retained = getattr(
            message,
            "retain",
            False,
        )

        try:
            raw_payload = (
                message.payload.decode(
                    "utf-8"
                )
            )
        except UnicodeDecodeError:
            return

        if retained:
            if (
                message.topic
                not in self._retained_restore_topics
            ):
                return

            self._adapter.restore_message(
                topic=message.topic,
                raw_payload=raw_payload,
            )
            return

        result = (
            self._adapter.ingest_message(
                topic=message.topic,
                raw_payload=raw_payload,
            )
        )

        if result is None:
            return

        if isinstance(
            result,
            list,
        ):
            observations = result
        else:
            observations = [
                result
            ]

        if not observations:
            return

        available_observations = []

        for observation in observations:
            if (
                getattr(
                    observation,
                    "quality",
                    "good",
                )
                == "unavailable"
            ):
                if (
                    self._observation_accumulator
                    is not None
                ):
                    self._observation_accumulator.withdraw(
                        observation.location_id,
                        observation.parameter,
                    )

                continue

            available_observations.append(
                observation
            )

        if not available_observations:
            return

        if (
            self._observation_accumulator
            is not None
        ):
            self._observation_accumulator.update(
                available_observations
            )

        location_ids = []

        for observation in (
            available_observations
        ):
            if (
                observation.location_id
                not in location_ids
            ):
                location_ids.append(
                    observation.location_id
                )

        if self._observation_sink is None:
            return

        for location_id in location_ids:
            if (
                self._observation_accumulator
                is not None
            ):
                current_observations = (
                    self._observation_accumulator
                    .for_location(
                        location_id
                    )
                )
            else:
                current_observations = [
                    observation
                    for observation
                    in available_observations
                    if (
                        observation.location_id
                        == location_id
                    )
                ]

            self._observation_sink.process(
                current_observations,
                location_id=location_id,
            )

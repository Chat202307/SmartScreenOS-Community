from __future__ import annotations

import threading


class XingooDeviceDataSource:
    def __init__(
        self,
        *,
        client,
        adapter,
        iot_ids,
        observation_accumulator=None,
        observation_sink=None,
        poll_interval_seconds=30.0,
        retry_interval_seconds=10.0,
    ):
        self._client = client
        self._adapter = adapter
        self._iot_ids = list(
            iot_ids or []
        )
        self._observation_accumulator = (
            observation_accumulator
        )
        self._observation_sink = (
            observation_sink
        )

        self._poll_interval_seconds = float(
            poll_interval_seconds
        )
        self._retry_interval_seconds = float(
            retry_interval_seconds
        )

        self._thread = None
        self._stop_event = threading.Event()
        self._refresh_lock = threading.Lock()

    def start(self):
        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_background,
            name="smartscreen-xingoo-device-data",
            daemon=False,
        )

        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def join(
        self,
        timeout=None,
    ):
        if self._thread is None:
            return

        self._thread.join(
            timeout=timeout
        )

    def is_alive(self):
        return (
            self._thread is not None
            and self._thread.is_alive()
        )

    def _run_background(self):
        while not self._stop_event.is_set():
            wait_seconds = (
                self._poll_interval_seconds
            )

            try:
                self.refresh()
            except Exception:
                if self._stop_event.is_set():
                    return

                wait_seconds = (
                    self._retry_interval_seconds
                )

            if self._stop_event.wait(
                timeout=wait_seconds
            ):
                return

    def refresh(self):
        with self._refresh_lock:
            return self._refresh_once()

    def _refresh_once(self):
        observations_by_location = {}

        for iot_id in self._iot_ids:
            properties = (
                self._client
                .get_all_properties(
                    iot_id=iot_id,
                )
            )

            observations = (
                self._adapter
                .ingest_properties(
                    iot_id=iot_id,
                    properties=properties,
                )
            )

            for observation in observations:
                location_id = (
                    observation.location_id
                )

                observations_by_location.setdefault(
                    location_id,
                    [],
                ).append(
                    observation
                )

        result = []

        for (
            location_id,
            observations,
        ) in observations_by_location.items():
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
                            location_id,
                            observation.parameter,
                        )

                    continue

                available_observations.append(
                    observation
                )

            if (
                self._observation_accumulator
                is not None
            ):
                if available_observations:
                    self._observation_accumulator.update(
                        available_observations
                    )

                current_observations = (
                    self._observation_accumulator
                    .for_location(
                        location_id
                    )
                )

            else:
                current_observations = (
                    available_observations
                )

            result.extend(
                current_observations
            )

            if (
                self._observation_sink
                is not None
            ):
                self._observation_sink.process(
                    current_observations,
                    location_id=location_id,
                )

        return result

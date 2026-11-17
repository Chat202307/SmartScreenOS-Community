from __future__ import annotations

from threading import Event, Thread


class ObservationFreshnessSweep:
    """Periodically re-evaluate known observation locations."""

    def __init__(
        self,
        *,
        accumulator,
        observation_sink,
        interval_seconds=5.0,
    ):
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        self._accumulator = accumulator
        self._observation_sink = observation_sink
        self._interval_seconds = float(
            interval_seconds
        )

        self._stop_event = Event()
        self._thread = None

    def run_once(self):
        locations = list(
            self._accumulator.locations()
        )

        for location_id in locations:
            observations = (
                self._accumulator.for_location(
                    location_id
                )
            )

            self._observation_sink.process(
                observations,
                location_id=location_id,
            )

        return len(locations)

    def start(self):
        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            name="observation-freshness-sweep",
            daemon=True,
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

    def _run(self):
        while not self._stop_event.wait(
            self._interval_seconds
        ):
            self.run_once()

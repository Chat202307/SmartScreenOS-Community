from __future__ import annotations

import threading
import time
from typing import Any, Callable, Protocol


class TickEngine(Protocol):
    def tick(self) -> Any:
        """Run one runtime maintenance cycle."""


class RuntimeScheduler:
    """Trigger runtime ticks at a fixed interval."""

    def __init__(
        self,
        engine: TickEngine,
        *,
        interval_seconds: float,
        start_time: float,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
        loop_sleep_seconds: float = 0.1,
    ) -> None:
        if (
            not isinstance(interval_seconds, (int, float))
            or isinstance(interval_seconds, bool)
            or interval_seconds <= 0
        ):
            raise ValueError(
                "Scheduler interval must be greater than zero."
            )

        if (
            not isinstance(loop_sleep_seconds, (int, float))
            or isinstance(loop_sleep_seconds, bool)
            or loop_sleep_seconds <= 0
        ):
            raise ValueError(
                "Scheduler loop sleep interval must be greater than zero."
            )

        self._engine = engine
        self._interval_seconds = float(interval_seconds)
        self._next_run_at = float(start_time) + self._interval_seconds
        self._running = True

        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._loop_sleep_seconds = float(loop_sleep_seconds)

        self._background_thread: threading.Thread | None = None
        self._background_lock = threading.Lock()
        self._last_background_error: Exception | None = None

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    @property
    def next_run_at(self) -> float:
        return self._next_run_at

    @property
    def running(self) -> bool:
        return self._running

    @property
    def loop_sleep_seconds(self) -> float:
        return self._loop_sleep_seconds

    @property
    def background_running(self) -> bool:
        thread = self._background_thread
        return thread is not None and thread.is_alive()

    @property
    def last_background_error(self) -> Exception | None:
        return self._last_background_error

    @property
    def background_failed(self) -> bool:
        return self._last_background_error is not None

    def start(self, *, now: float) -> None:
        if self._running:
            return

        self._running = True
        self._next_run_at = float(now) + self._interval_seconds

    def stop(self) -> None:
        self._running = False

    def reset(self, *, now: float) -> None:
        self._next_run_at = float(now) + self._interval_seconds

    def poll(self, *, now: float):
        if not self._running:
            return None

        if now < self._next_run_at:
            return None

        result = self._engine.tick()
        self._next_run_at = float(now) + self._interval_seconds

        return result

    def run_once(self):
        """Poll once using the configured clock."""
        return self.poll(now=self._clock())

    def run(self) -> None:
        """Run continuously until stop() is called."""
        while self._running:
            self.run_once()
            self._sleep(self._loop_sleep_seconds)

    def _run_background(self) -> None:
        """Run the scheduler loop and capture unexpected failures."""

        try:
            self.run()
        except Exception as exc:
            self._last_background_error = exc
            self._running = False

    def start_background(self) -> None:
        """Start the scheduler loop in a background thread."""

        with self._background_lock:
            if self.background_running:
                return

            self._last_background_error = None

            if not self._running:
                self.start(now=self._clock())

            thread = threading.Thread(
                target=self._run_background,
                name="SmartScreenRuntimeScheduler",
                daemon=True,
            )

            self._background_thread = thread
            thread.start()

    def stop_background(self) -> None:
        """Request the background scheduler loop to stop."""
        self.stop()

    def join(self, timeout: float | None = None) -> None:
        """Wait for the background scheduler thread to finish."""

        thread = self._background_thread

        if thread is None:
            return

        thread.join(timeout=timeout)

from __future__ import annotations

import threading


class HouseholdStateChangeNotifier:
    def __init__(self) -> None:
        self._revision = 0
        self._condition = threading.Condition()

    @property
    def revision(self) -> int:
        with self._condition:
            return self._revision

    def notify(self) -> int:
        with self._condition:
            self._revision += 1
            self._condition.notify_all()
            return self._revision

    def wait_for_change(
        self,
        revision: int,
        *,
        timeout: float | None = None,
    ) -> int:
        with self._condition:
            self._condition.wait_for(
                lambda: self._revision != revision,
                timeout=timeout,
            )

            return self._revision

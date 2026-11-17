from copy import deepcopy
from threading import RLock


class StateChangeDetector:
    def __init__(self):
        self._lock = RLock()
        self._last = {}

    def evaluate(self, device_id, available, state, attributes):
        current = {
            "available": bool(available),
            "state": str(state),
            "attributes": deepcopy(dict(attributes or {})),
        }

        with self._lock:
            previous = self._last.get(device_id)
            self._last[device_id] = deepcopy(current)

        changed = previous != current

        return {
            "changed": changed,
            "previous": deepcopy(previous),
            "current": deepcopy(current),
        }

from copy import deepcopy
from threading import RLock

class HomeEventBus:
    def __init__(self, history_limit=200):
        self._lock = RLock()
        self._subscribers = {}
        self._history = []
        self._history_limit = int(history_limit)

    def subscribe(self, event_type, callback):
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event):
        with self._lock:
            self._history.append(event)
            self._history = self._history[-self._history_limit:]
            callbacks = list(self._subscribers.get(event.event_type, []))
            callbacks += list(self._subscribers.get('*', []))
        for callback in callbacks:
            callback(event)

    def snapshot(self, limit=50):
        with self._lock:
            items = self._history[-int(limit):]
        return [deepcopy(item.to_dict()) for item in reversed(items)]

    def stats(self):
        with self._lock:
            return {
                'history_count': len(self._history),
                'subscriber_groups': len(self._subscribers),
                'subscriber_count': sum(len(items) for items in self._subscribers.values()),
            }

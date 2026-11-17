from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class Event:
    name: str
    source: str
    payload: Dict[str, Any]
    created_at: str


class EventBus:
    def __init__(self, history_limit=200):
        self._lock = RLock()
        self._history_limit = int(history_limit)
        self._subscribers = {}
        self._history = []
        self._published_count = 0

    def subscribe(self, event_name: str, callback: Callable[[Event], None]):
        with self._lock:
            self._subscribers.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback):
        with self._lock:
            callbacks = self._subscribers.get(event_name, [])
            self._subscribers[event_name] = [
                item for item in callbacks if item is not callback
            ]

    def publish(self, event_name: str, source: str, payload=None):
        event = Event(
            name=event_name,
            source=source,
            payload=dict(payload or {}),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._published_count += 1
            self._history.append(event)
            self._history = self._history[-self._history_limit:]

            callbacks = list(self._subscribers.get(event_name, []))
            callbacks.extend(self._subscribers.get("*", []))

        for callback in callbacks:
            try:
                callback(event)
            except Exception as exc:
                print(
                    "[EVENT ERROR]",
                    event_name,
                    getattr(callback, "__name__", repr(callback)),
                    exc,
                )

        return event

    def recent(self, limit=50):
        with self._lock:
            items = self._history[-int(limit):]
            return list(reversed(items))

    def stats(self):
        with self._lock:
            return {
                "published_count": self._published_count,
                "history_count": len(self._history),
                "subscriber_groups": len(self._subscribers),
                "subscriber_count": sum(
                    len(items)
                    for items in self._subscribers.values()
                ),
            }

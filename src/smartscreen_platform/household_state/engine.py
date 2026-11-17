from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock

from src.smartscreen_platform.contracts.state import HouseholdStateEntry


class HouseholdStateEngine:
    def __init__(
        self,
        history_limit=100,
        *,
        clock=None,
        change_notifier=None,
    ):
        self._lock = RLock()
        self._entries = {}
        self._history = []
        self._history_limit = int(history_limit)
        self._clock = (
            clock
            if clock is not None
            else lambda: datetime.now(timezone.utc)
        )
        self._change_notifier = change_notifier

    @staticmethod
    def _key(target, location_id):
        return (location_id, target)

    def apply(self, patch):
        key = self._key(patch.target, patch.location_id)

        with self._lock:
            current = self._entries.get(key)

            if (
                current is not None
                and self._is_expired(current)
            ):
                del self._entries[key]
                current = None

            if (
                current is not None
                and patch.confidence < current.confidence
            ):
                return current

            entry = HouseholdStateEntry(
                target=patch.target,
                value=deepcopy(patch.value),
                confidence=patch.confidence,
                updated_at=patch.created_at,
                ttl_seconds=patch.ttl_seconds,
                location_id=patch.location_id,
                source_capability=patch.capability,
                evidence_refs=list(patch.evidence_refs),
                metadata=deepcopy(patch.metadata),
            )

            self._entries[key] = entry
            self._history.append(entry)
            self._history = self._history[-self._history_limit:]
            self._notify_change()
            return entry

    def get(self, target, location_id=None):
        key = self._key(
            target,
            location_id,
        )

        with self._lock:
            entry = self._entries.get(key)

            if (
                entry is not None
                and self._is_expired(entry)
            ):
                del self._entries[key]
                self._notify_change()
                return None

            return entry

    def remove(
        self,
        target,
        location_id=None,
    ):
        key = self._key(
            target,
            location_id,
        )

        with self._lock:
            if key not in self._entries:
                return False

            del self._entries[key]
            self._notify_change()
            return True

    def snapshot(self):
        with self._lock:
            self._remove_expired()

            return [
                deepcopy(item.to_dict())
                for item in self._entries.values()
            ]

    def _remove_expired(self):
        expired_keys = [
            key
            for key, entry in self._entries.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self._entries[key]

        if expired_keys:
            self._notify_change()

    def _notify_change(self):
        if self._change_notifier is not None:
            self._change_notifier.notify()

    def _is_expired(self, entry):
        updated_at = datetime.fromisoformat(
            entry.updated_at
        )

        age_seconds = (
            self._clock() - updated_at
        ).total_seconds()

        return (
            age_seconds
            > entry.ttl_seconds
        )

    def history(self, limit=20):
        with self._lock:
            items = self._history[-int(limit):]
            return [deepcopy(item.to_dict()) for item in reversed(items)]

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


class CalendarSourceError(RuntimeError):
    """A sanitized calendar upstream failure suitable for the HTTP boundary."""


class CalendarSyncPending(CalendarSourceError):
    def __init__(self, state='syncing', retry_after=1):
        super().__init__('calendar service unavailable')
        self.retry_after = max(1, min(30, int(retry_after)))
        self.status = dict(state=state if state in ('syncing', 'unavailable', 'stopped') else 'unavailable',
                           stale=False, age_seconds=None, last_success_at=None)


@dataclass(frozen=True)
class CalendarEventOccurrence:
    event_id: str
    calendar_id: str
    title: str
    start: datetime
    end: datetime
    all_day: bool

    def __post_init__(self) -> None:
        if not str(self.event_id).strip():
            raise ValueError("event_id is required")

        if not str(self.calendar_id).strip():
            raise ValueError("calendar_id is required")

        if comparable_time(self.end) < comparable_time(self.start):
            raise ValueError(
                "end must not be before start"
            )

    @property
    def occurrence_id(self) -> str:
        return (
            self.event_id
            + "@"
            + self.start.isoformat()
        )


class CalendarEventService:
    def __init__(
        self,
        *,
        source,
        calendar_id: str | None = None,
    ) -> None:
        resolved_calendar_id = None

        if calendar_id is not None:
            resolved_calendar_id = str(
                calendar_id
            ).strip()

            if not resolved_calendar_id:
                raise ValueError(
                    "calendar_id must be non-blank or None"
                )

        self._source = source
        self._calendar_id = resolved_calendar_id

    def list_events(
        self,
        *,
        start: datetime,
        end: datetime,
    ) -> tuple[CalendarEventOccurrence, ...]:
        return self.snapshot(start=start, end=end)[0]

    def snapshot(self, *, start: datetime, end: datetime):
        events, status = self.snapshot_details(start=start, end=end)
        return events, bool(status and status["stale"])

    def snapshot_details(self, *, start: datetime, end: datetime):
        details = getattr(self._source, "snapshot_details", None)
        snapshot = getattr(self._source, "snapshot", None)
        if details is not None:
            events, status = details(start, end)
        elif snapshot is None:
            events, status = self._source.list_events(start, end), None
        else:
            events, stale = snapshot(start, end)
            status = {"stale": stale}

        matching_events = (
            event
            for event in events
            if (
                self._calendar_id is None
                or event.calendar_id == self._calendar_id
            )
        )

        return tuple(
            sorted(
                matching_events,
                key=lambda event: (
                    comparable_time(event.start),
                    comparable_time(event.end),
                    event.occurrence_id,
                ),
            )
        ), status


def comparable_time(value: datetime) -> datetime:
    """Compare aware instants in UTC, including the repeated hour at DST end."""
    return value.astimezone(timezone.utc) if value.tzinfo is not None else value

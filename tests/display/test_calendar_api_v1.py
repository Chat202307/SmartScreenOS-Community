import json
from datetime import datetime

from src.smartscreen_display.calendar_source import (
    CalendarEventOccurrence,
)
from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {}


class FakeCalendarEventService:
    def __init__(self):
        self.calls = []

    def list_events(self, *, start, end):
        self.calls.append(
            {
                "start": start,
                "end": end,
            }
        )
        return (
            CalendarEventOccurrence(
                event_id="event-1",
                calendar_id="calendar-1",
                title="家庭重要日期",
                start=datetime.fromisoformat(
                    "2026-10-06T00:00:00+08:00"
                ),
                end=datetime.fromisoformat(
                    "2026-10-06T23:59:59+08:00"
                ),
                all_day=True,
            ),
        )


def test_calendar_api_returns_events():
    service = FakeCalendarEventService()

    app = SnapshotApplication(
        FakeHost(),
        calendar_event_service=service,
    )

    status, headers, body = app.handle(
        method="GET",
        path=(
            "/api/calendar"
            "?start=2026-10-01T00:00:00%2B08:00"
            "&end=2026-11-01T00:00:00%2B08:00"
        ),
    )

    assert status == 200
    assert (
        headers["Content-Type"]
        == "application/json; charset=utf-8"
    )

    payload = json.loads(body.decode("utf-8"))

    assert payload == {
        "events": [
            {
                "event_id": "event-1",
                "calendar_id": "calendar-1",
                "title": "家庭重要日期",
                "start": "2026-10-06T00:00:00+08:00",
                "end": "2026-10-06T23:59:59+08:00",
                "all_day": True,
            }
        ]
    }

    assert service.calls == [
        {
            "start": datetime.fromisoformat(
                "2026-10-01T00:00:00+08:00"
            ),
            "end": datetime.fromisoformat(
                "2026-11-01T00:00:00+08:00"
            ),
        }
    ]


def test_calendar_api_is_read_only():
    app = SnapshotApplication(
        FakeHost(),
        calendar_event_service=FakeCalendarEventService(),
    )

    status, headers, body = app.handle(
        method="POST",
        path="/api/calendar",
    )

    assert status == 405
    assert headers["Allow"] == "GET"

    payload = json.loads(body.decode("utf-8"))
    assert payload == {
        "error": "method not allowed",
    }


def test_calendar_api_returns_503_when_service_unavailable():
    app = SnapshotApplication(
        FakeHost(),
        calendar_event_service=None,
    )

    status, headers, body = app.handle(
        method="GET",
        path=(
            "/api/calendar"
            "?start=2026-10-01T00:00:00%2B08:00"
            "&end=2026-11-01T00:00:00%2B08:00"
        ),
    )

    assert status == 503
    assert (
        headers["Content-Type"]
        == "application/json; charset=utf-8"
    )

    payload = json.loads(body.decode("utf-8"))
    assert payload == {
        "error": "calendar service unavailable",
    }


def test_calendar_api_requires_start_and_end():
    app = SnapshotApplication(
        FakeHost(),
        calendar_event_service=FakeCalendarEventService(),
    )

    status, headers, body = app.handle(
        method="GET",
        path="/api/calendar",
    )

    assert status == 400

    payload = json.loads(body.decode("utf-8"))
    assert payload == {
        "error": "start and end required",
    }


def test_calendar_api_rejects_invalid_datetime():
    app = SnapshotApplication(
        FakeHost(),
        calendar_event_service=FakeCalendarEventService(),
    )

    status, headers, body = app.handle(
        method="GET",
        path=(
            "/api/calendar"
            "?start=not-a-date"
            "&end=2026-11-01T00:00:00%2B08:00"
        ),
    )

    assert status == 400

    payload = json.loads(body.decode("utf-8"))
    assert payload == {
        "error": "invalid calendar range",
    }


def test_calendar_api_rejects_end_before_start():
    app = SnapshotApplication(
        FakeHost(),
        calendar_event_service=FakeCalendarEventService(),
    )

    status, headers, body = app.handle(
        method="GET",
        path=(
            "/api/calendar"
            "?start=2026-11-01T00:00:00%2B08:00"
            "&end=2026-10-01T00:00:00%2B08:00"
        ),
    )

    assert status == 400

    payload = json.loads(body.decode("utf-8"))
    assert payload == {
        "error": "invalid calendar range",
    }

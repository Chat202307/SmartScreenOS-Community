from datetime import datetime

import pytest


def test_calendar_event_occurrence_has_stable_occurrence_id():
    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
    )

    event = CalendarEventOccurrence(
        event_id="event-123",
        calendar_id="calendar-456",
        title="结婚纪念日",
        start=datetime(2026, 10, 29, 0, 0, 0),
        end=datetime(2026, 10, 29, 23, 59, 59),
        all_day=True,
    )

    assert event.event_id == "event-123"
    assert event.calendar_id == "calendar-456"
    assert event.title == "结婚纪念日"
    assert event.all_day is True

    assert event.occurrence_id == (
        "event-123@2026-10-29T00:00:00"
    )


def test_occurrences_of_same_recurring_event_have_different_ids():
    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
    )

    october = CalendarEventOccurrence(
        event_id="recurring-event",
        calendar_id="family-calendar",
        title="花呗还款日",
        start=datetime(2026, 10, 9, 0, 0, 0),
        end=datetime(2026, 10, 9, 23, 59, 59),
        all_day=True,
    )

    november = CalendarEventOccurrence(
        event_id="recurring-event",
        calendar_id="family-calendar",
        title="花呗还款日",
        start=datetime(2026, 11, 9, 0, 0, 0),
        end=datetime(2026, 11, 9, 23, 59, 59),
        all_day=True,
    )

    assert october.event_id == november.event_id
    assert october.occurrence_id != november.occurrence_id


def test_calendar_event_occurrence_rejects_blank_identity():
    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
    )

    with pytest.raises(ValueError):
        CalendarEventOccurrence(
            event_id="",
            calendar_id="family-calendar",
            title="结婚纪念日",
            start=datetime(2026, 10, 29),
            end=datetime(2026, 10, 30),
            all_day=True,
        )

    with pytest.raises(ValueError):
        CalendarEventOccurrence(
            event_id="event-123",
            calendar_id="",
            title="结婚纪念日",
            start=datetime(2026, 10, 29),
            end=datetime(2026, 10, 30),
            all_day=True,
        )


def test_calendar_event_occurrence_rejects_end_before_start():
    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
    )

    with pytest.raises(ValueError):
        CalendarEventOccurrence(
            event_id="event-123",
            calendar_id="family-calendar",
            title="结婚纪念日",
            start=datetime(2026, 10, 30),
            end=datetime(2026, 10, 29),
            all_day=True,
        )


class FakeCalendarSource:
    def __init__(self, events):
        self.events = tuple(events)
        self.calls = []

    def list_events(self, start, end):
        self.calls.append((start, end))
        return self.events


def test_calendar_event_service_filters_target_calendar_and_sorts():
    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
        CalendarEventService,
    )

    source = FakeCalendarSource(
        [
            CalendarEventOccurrence(
                event_id="event-later",
                calendar_id="family-calendar",
                title="结婚纪念日",
                start=datetime(2026, 10, 29),
                end=datetime(2026, 10, 29, 23, 59, 59),
                all_day=True,
            ),
            CalendarEventOccurrence(
                event_id="other-event",
                calendar_id="other-calendar",
                title="不应显示",
                start=datetime(2026, 10, 8),
                end=datetime(2026, 10, 8, 23, 59, 59),
                all_day=True,
            ),
            CalendarEventOccurrence(
                event_id="event-earlier",
                calendar_id="family-calendar",
                title="结婚纪念日测试",
                start=datetime(2026, 10, 16),
                end=datetime(2026, 10, 16, 23, 59, 59),
                all_day=True,
            ),
        ]
    )

    service = CalendarEventService(
        source=source,
        calendar_id="family-calendar",
    )

    start = datetime(2026, 10, 6)
    end = datetime(2026, 11, 6)

    events = service.list_events(
        start=start,
        end=end,
    )

    assert source.calls == [(start, end)]

    assert [
        event.title
        for event in events
    ] == [
        "结婚纪念日测试",
        "结婚纪念日",
    ]


def test_calendar_event_service_keeps_recurring_occurrences():
    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
        CalendarEventService,
    )

    source = FakeCalendarSource(
        [
            CalendarEventOccurrence(
                event_id="recurring-event",
                calendar_id="family-calendar",
                title="花呗还款日",
                start=datetime(2026, 10, 9),
                end=datetime(2026, 10, 9, 23, 59, 59),
                all_day=True,
            ),
            CalendarEventOccurrence(
                event_id="recurring-event",
                calendar_id="family-calendar",
                title="花呗还款日",
                start=datetime(2026, 11, 9),
                end=datetime(2026, 11, 9, 23, 59, 59),
                all_day=True,
            ),
        ]
    )

    service = CalendarEventService(
        source=source,
        calendar_id="family-calendar",
    )

    events = service.list_events(
        start=datetime(2026, 10, 1),
        end=datetime(2026, 12, 1),
    )

    assert len(events) == 2
    assert events[0].occurrence_id != events[1].occurrence_id


def test_calendar_event_service_requires_calendar_identity():
    from src.smartscreen_display.calendar_source import (
        CalendarEventService,
    )

    with pytest.raises(ValueError):
        CalendarEventService(
            source=FakeCalendarSource([]),
            calendar_id="",
        )


def test_calendar_event_service_all_calendars():
    from datetime import datetime

    from src.smartscreen_display.calendar_source import (
        CalendarEventOccurrence,
        CalendarEventService,
    )

    class Source:
        def list_events(self, start, end):
            return (
                CalendarEventOccurrence(
                    event_id="event-b",
                    calendar_id="calendar-b",
                    title="B",
                    start=datetime.fromisoformat(
                        "2026-10-09T00:00:00+08:00"
                    ),
                    end=datetime.fromisoformat(
                        "2026-10-09T23:59:59+08:00"
                    ),
                    all_day=True,
                ),
                CalendarEventOccurrence(
                    event_id="event-a",
                    calendar_id="calendar-a",
                    title="A",
                    start=datetime.fromisoformat(
                        "2026-10-08T00:00:00+08:00"
                    ),
                    end=datetime.fromisoformat(
                        "2026-10-08T23:59:59+08:00"
                    ),
                    all_day=True,
                ),
            )

    service = CalendarEventService(
        source=Source(),
        calendar_id=None,
    )

    events = service.list_events(
        start=datetime.fromisoformat(
            "2026-10-07T00:00:00+08:00"
        ),
        end=datetime.fromisoformat(
            "2026-10-17T00:00:00+08:00"
        ),
    )

    assert [event.title for event in events] == [
        "A",
        "B",
    ]

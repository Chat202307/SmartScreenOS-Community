from datetime import datetime

import pytest


def test_eventkit_source_builds_request_contract():
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitCalendarSource,
    )

    captured = {}

    def runner(payload):
        captured["payload"] = payload
        return {"events": []}

    source = EventKitCalendarSource(
        runner=runner,
    )

    result = source.list_events(
        datetime(2026, 10, 6, 0, 0, 0),
        datetime(2027, 10, 6, 0, 0, 0),
    )

    assert result == ()
    assert captured["payload"] == {
        "start": "2026-10-06T00:00:00",
        "end": "2027-10-06T00:00:00",
    }


def test_eventkit_source_maps_response_to_occurrences():
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitCalendarSource,
    )

    def runner(payload):
        return {
            "events": [
                {
                    "event_id": "event-123",
                    "calendar_id": "family-calendar",
                    "title": "结婚纪念日",
                    "start": "2026-10-29T00:00:00",
                    "end": "2026-10-29T23:59:59",
                    "all_day": True,
                }
            ]
        }

    source = EventKitCalendarSource(
        runner=runner,
    )

    events = source.list_events(
        datetime(2026, 10, 1),
        datetime(2026, 11, 1),
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_id == "event-123"
    assert event.calendar_id == "family-calendar"
    assert event.title == "结婚纪念日"
    assert event.start == datetime(
        2026,
        10,
        29,
        0,
        0,
        0,
    )
    assert event.end == datetime(
        2026,
        10,
        29,
        23,
        59,
        59,
    )
    assert event.all_day is True


def test_eventkit_source_keeps_recurring_occurrences():
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitCalendarSource,
    )

    def runner(payload):
        return {
            "events": [
                {
                    "event_id": "recurring-123",
                    "calendar_id": "family-calendar",
                    "title": "花呗还款日",
                    "start": "2026-10-09T00:00:00",
                    "end": "2026-10-09T23:59:59",
                    "all_day": True,
                },
                {
                    "event_id": "recurring-123",
                    "calendar_id": "family-calendar",
                    "title": "花呗还款日",
                    "start": "2026-11-09T00:00:00",
                    "end": "2026-11-09T23:59:59",
                    "all_day": True,
                },
            ]
        }

    source = EventKitCalendarSource(
        runner=runner,
    )

    events = source.list_events(
        datetime(2026, 10, 1),
        datetime(2026, 12, 1),
    )

    assert len(events) == 2
    assert events[0].event_id == events[1].event_id
    assert (
        events[0].occurrence_id
        != events[1].occurrence_id
    )


def test_eventkit_source_rejects_invalid_response():
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitCalendarSource,
    )

    def runner(payload):
        return {
            "events": [
                {
                    "event_id": "",
                    "calendar_id": "family-calendar",
                    "title": "结婚纪念日",
                    "start": "2026-10-29T00:00:00",
                    "end": "2026-10-29T23:59:59",
                    "all_day": True,
                }
            ]
        }

    source = EventKitCalendarSource(
        runner=runner,
    )

    with pytest.raises(ValueError):
        source.list_events(
            datetime(2026, 10, 1),
            datetime(2026, 11, 1),
        )


def test_eventkit_source_rejects_invalid_range():
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitCalendarSource,
    )

    source = EventKitCalendarSource(
        runner=lambda payload: {"events": []},
    )

    with pytest.raises(ValueError):
        source.list_events(
            datetime(2026, 11, 1),
            datetime(2026, 10, 1),
        )


def test_eventkit_subprocess_runner_exchanges_json(tmp_path):
    import json

    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitSubprocessRunner,
    )

    bridge = tmp_path / "bridge"
    bridge.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "import sys\n"
        "payload = json.load(sys.stdin)\n"
        "json.dump({\n"
        "    'events': [],\n"
        "    'received': payload,\n"
        "}, sys.stdout)\n"
    )
    bridge.chmod(0o755)

    runner = EventKitSubprocessRunner(
        executable=bridge,
    )

    result = runner(
        {
            "start": "2026-10-06T00:00:00",
            "end": "2027-10-06T00:00:00",
        }
    )

    assert result == {
        "events": [],
        "received": {
            "start": "2026-10-06T00:00:00",
            "end": "2027-10-06T00:00:00",
        },
    }


def test_eventkit_subprocess_runner_rejects_bridge_failure(
    tmp_path,
):
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitBridgeError,
        EventKitSubprocessRunner,
    )

    bridge = tmp_path / "bridge"
    bridge.write_text(
        "#!/bin/sh\n"
        'echo "bridge failed" >&2\n'
        "exit 7\n"
    )
    bridge.chmod(0o755)

    runner = EventKitSubprocessRunner(
        executable=bridge,
    )

    with pytest.raises(
        EventKitBridgeError,
        match="bridge failed",
    ):
        runner(
            {
                "start": "2026-10-06T00:00:00",
                "end": "2027-10-06T00:00:00",
            }
        )


def test_eventkit_subprocess_runner_rejects_invalid_json(
    tmp_path,
):
    from src.smartscreen_display.eventkit_calendar_source import (
        EventKitBridgeError,
        EventKitSubprocessRunner,
    )

    bridge = tmp_path / "bridge"
    bridge.write_text(
        "#!/bin/sh\n"
        'printf "not-json"\n'
    )
    bridge.chmod(0o755)

    runner = EventKitSubprocessRunner(
        executable=bridge,
    )

    with pytest.raises(EventKitBridgeError):
        runner(
            {
                "start": "2026-10-06T00:00:00",
                "end": "2027-10-06T00:00:00",
            }
        )

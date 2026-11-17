from __future__ import annotations

from datetime import datetime

from .calendar_source import CalendarEventOccurrence


class EventKitCalendarSource:
    def __init__(self, *, runner) -> None:
        self._runner = runner

    def list_events(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[CalendarEventOccurrence, ...]:
        if end < start:
            raise ValueError(
                "end must not be before start"
            )

        response = self._runner(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        )

        events = response["events"]

        return tuple(
            CalendarEventOccurrence(
                event_id=item["event_id"],
                calendar_id=item["calendar_id"],
                title=item["title"],
                start=datetime.fromisoformat(
                    item["start"]
                ),
                end=datetime.fromisoformat(
                    item["end"]
                ),
                all_day=item["all_day"],
            )
            for item in events
        )


class EventKitBridgeError(RuntimeError):
    pass


class EventKitSubprocessRunner:
    def __init__(self, *, executable) -> None:
        from pathlib import Path

        self._executable = Path(executable)

    def __call__(self, payload):
        import json
        import subprocess

        try:
            completed = subprocess.run(
                [str(self._executable)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise EventKitBridgeError(
                "unable to start EventKit bridge: "
                + str(exc)
            ) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip()

            if not detail:
                detail = (
                    "EventKit bridge exited with status "
                    + str(completed.returncode)
                )

            raise EventKitBridgeError(detail)

        try:
            response = json.loads(completed.stdout)
        except (TypeError, json.JSONDecodeError) as exc:
            raise EventKitBridgeError(
                "EventKit bridge returned invalid JSON"
            ) from exc

        if not isinstance(response, dict):
            raise EventKitBridgeError(
                "EventKit bridge response must be an object"
            )

        return response

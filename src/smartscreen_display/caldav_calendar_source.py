"""Read-only CalDAV adapter; no macOS services or EventKit dependency.

Fetch complete recurrence sets with a bounded server time-range query, then
expand locally so EXDATE and detached RECURRENCE-ID overrides stay together.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import logging
import os
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from urllib.parse import urljoin

import caldav
from icalendar import Calendar
import recurring_ical_events

from .calendar_source import CalendarEventOccurrence, CalendarSourceError


@dataclass
class _CacheEntry:
    events: tuple[CalendarEventOccurrence, ...]
    fetched_at: float
    fetched_at_utc: str


@dataclass
class _FetchTask:
    done: Event
    events: tuple[CalendarEventOccurrence, ...] = ()
    failed: bool = False


class CalDAVCalendarSource:
    CACHE_SECONDS = 300
    RETRY_SECONDS = 30
    MAX_STALE_SECONDS = 3600
    MAX_RANGES = 8
    MAX_RANGE = timedelta(days=366)
    MAX_RESOURCE_BYTES = 2 * 1024 * 1024
    MAX_TOTAL_BYTES = 16 * 1024 * 1024
    MAX_COMPONENTS = 10000
    MAX_OCCURRENCES = 10000

    def __init__(self, *, config, client_factory=caldav.DAVClient,
                 clock=monotonic, environ=None, credential_provider=None) -> None:
        self._credential_provider = credential_provider
        self._config = config
        self._timezone = ZoneInfo(config.timezone)
        self._client_factory = client_factory
        self._clock = clock
        self._environ = os.environ if environ is None else environ
        self._cache = OrderedDict()
        self._retry_at = 0.0
        self._lock = Lock()
        self._pending = None

    def _aware(self, value: date | datetime) -> datetime:
        if not isinstance(value, datetime):
            return datetime.combine(value, time.min, self._timezone)
        if value.tzinfo is None:
            return value.replace(tzinfo=self._timezone)
        return value

    def _localize_floating(self, component):
        # Do not use X-WR-TIMEZONE correction: rewriting already-aware UTC
        # values can lose the relationship to RECURRENCE-ID overrides.
        def localize(value, params):
            if isinstance(value, datetime) and value.tzinfo is None:
                if params.get("TZID"):
                    raise ValueError("unresolved calendar timezone")
                return value.replace(tzinfo=self._timezone)
            if isinstance(value, tuple):
                return tuple(localize(part, params) for part in value)
            return value
        for name in ("DTSTART", "DTEND", "RECURRENCE-ID", "EXDATE", "RDATE"):
            properties = component.get(name, [])
            if not isinstance(properties, list):
                properties = [properties]
            for prop in properties:
                if hasattr(prop, "dts"):
                    for value in prop.dts:
                        value.dt = localize(value.dt, prop.params)
                elif hasattr(prop, "dt"):
                    prop.dt = localize(prop.dt, prop.params)
        start = component.get("DTSTART")
        if start is not None and isinstance(start.dt, datetime):
            for name in ("RRULE", "EXRULE"):
                rules = component.get(name, [])
                if not isinstance(rules, list):
                    rules = [rules]
                for rule in rules:
                    if "UNTIL" in rule:
                        rule["UNTIL"] = [
                            localize(value, {}).astimezone(timezone.utc)
                            if isinstance(value, datetime) and value.tzinfo is None else value
                            for value in rule["UNTIL"]
                        ]

    def list_events(self, start: datetime, end: datetime):
        # Keep the existing list_events contract; HTTP also uses snapshot below
        # to attach an atomic stale flag without a cross-request status race.
        return self.snapshot(start, end)[0]

    def snapshot(self, start: datetime, end: datetime):
        events, status = self.snapshot_details(start, end)
        return events, status["stale"]

    def _status(self, entry, *, stale):
        return {
            "state": "stale" if stale else "fresh",
            "stale": stale,
            "age_seconds": max(0, int(self._clock() - entry.fetched_at)),
            "last_success_at": entry.fetched_at_utc,
        }

    def snapshot_details(self, start: datetime, end: datetime):
        deadline = monotonic() + self._config.refresh_timeout_seconds
        start, end = self._aware(start), self._aware(end)
        try:
            start_utc, end_utc = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
            # Reserve the padding required by the server query below.
            start_utc - timedelta(days=1)
            end_utc + timedelta(days=1)
        except (ValueError, OverflowError):
            raise ValueError("invalid calendar range") from None
        if end_utc < start_utc or end_utc - start_utc > self.MAX_RANGE:
            raise ValueError("calendar range must be ordered and at most 366 days")
        if start_utc == end_utc:
            return (), {"state": "fresh", "stale": False, "age_seconds": 0,
                        "last_success_at": None}
        key = (start_utc, end_utc)
        # Serialize discovery/refresh. A session is never shared across threads.
        if not self._lock.acquire(timeout=max(0, deadline - monotonic())):
            raise CalendarSourceError("calendar service unavailable") from None
        try:
            now = self._clock()
            entry = self._cache.get(key)
            if entry is not None:
                self._cache.move_to_end(key)
                if now - entry.fetched_at < self.CACHE_SECONDS:
                    return entry.events, self._status(entry, stale=False)
            if now >= self._retry_at:
                try:
                    events = self._refresh(start_utc, end_utc, deadline)
                except Exception:
                    # Do not propagate upstream bodies/URLs/credentials or chain
                    # their exceptions into HTTP logs or tracebacks.
                    self._retry_at = self._clock() + self.RETRY_SECONDS
                    logging.getLogger(__name__).warning("CalDAV refresh failed; retry delayed")
                else:
                    self._retry_at = 0.0
                    self._cache[key] = _CacheEntry(
                        events, self._clock(), datetime.now(timezone.utc).isoformat()
                    )
                    self._cache.move_to_end(key)
                    while len(self._cache) > self.MAX_RANGES:
                        self._cache.popitem(last=False)
                    return events, self._status(self._cache[key], stale=False)
            if (self._config.allow_stale and entry is not None
                    and self._clock() - entry.fetched_at < self.MAX_STALE_SECONDS):
                return entry.events, self._status(entry, stale=True)
            raise CalendarSourceError("calendar service unavailable") from None
        finally:
            self._lock.release()

    def _refresh(self, start, end, deadline):
        # One daemon worker per source at most. A timed-out task is never used
        # to refresh the cache and never causes an unbounded queue of workers.
        # Python cannot kill a stuck network/library call; leave it quarantined
        # until it finishes while HTTP callers receive a bounded failure.
        if self._pending is not None and not self._pending.done.is_set():
            raise CalendarSourceError("calendar refresh still running")
        task = _FetchTask(Event())
        self._pending = task
        def run():
            try:
                task.events = self._fetch(start, end)
            except Exception:
                task.failed = True
            finally:
                task.done.set()
        Thread(target=run, name="caldav-refresh", daemon=True).start()
        if not task.done.wait(timeout=max(0, deadline - monotonic())):
            raise CalendarSourceError("calendar refresh timed out")
        self._pending = None
        if task.failed:
            raise CalendarSourceError("calendar refresh failed")
        return task.events

    @staticmethod
    def _resources(client, calendar, start, end):
        if not isinstance(calendar, caldav.Calendar):
            # Injected in-memory transports used by unit tests.
            return calendar.search(start=start, end=end, event=True,
                                   expand=False, post_filter=False)
        # DAVClient.report preserves raw calendar-data. Calendar.search silently
        # discards resources without a recognizable component, even with
        # post_filter=False, which could publish a partial calendar as fresh.
        stamp = lambda value: value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        query = (f'<c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">'
                 f'<d:prop><c:calendar-data/></d:prop><c:filter>'
                 f'<c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT">'
                 f'<c:time-range start="{stamp(start)}" end="{stamp(end)}"/>'
                 f'</c:comp-filter></c:comp-filter></c:filter></c:calendar-query>')
        response = client.report(str(calendar.url), query, depth=1)
        if response.status != 207 or response.tree is None:
            raise ValueError("incomplete calendar report")
        resources = []
        for item in response.tree.findall("{DAV:}response"):
            href = item.findtext("{DAV:}href")
            if not href:
                raise ValueError("missing calendar resource URL")
            if urljoin(str(calendar.url), href).rstrip("/") == str(calendar.url).rstrip("/"):
                continue  # iCloud may also return the collection itself.
            data = []
            for propstat in item.findall("{DAV:}propstat"):
                status = propstat.findtext("{DAV:}status", "").split()
                if len(status) < 2 or status[1] != "200":
                    raise ValueError("failed calendar resource")
                data.extend(propstat.findall("{DAV:}prop/{urn:ietf:params:xml:ns:caldav}calendar-data"))
            if len(data) != 1 or not data[0].text:
                raise ValueError("missing calendar resource data")
            resources.append(SimpleNamespace(data=data[0].text))
        return resources

    def _fetch(self, start: datetime, end: datetime):
        deadline = monotonic() + self._config.refresh_timeout_seconds
        if self._credential_provider is not None:
            # Local acceptance harness can keep credentials entirely in memory.
            username, password = self._credential_provider()
        else:
            if self._config.username_file_env:
                username_path = self._environ.get(self._config.username_file_env, '')
                if not username_path:
                    raise CalendarSourceError('calendar credentials unavailable')
                username = Path(username_path).read_text(encoding='utf-8').strip()
            else:
                username = self._environ.get(self._config.username_env, "").strip()
            password_path = self._environ.get(self._config.password_file_env, "")
            if not username or not password_path:
                raise CalendarSourceError("calendar credentials unavailable")
            password = Path(password_path).read_text(encoding="utf-8").strip()
        if not username or not password:
            raise CalendarSourceError("calendar credentials unavailable")

        client = self._client_factory(
            url=self._config.url, username=username, password=password,
            timeout=self._config.timeout_seconds, ssl_verify_cert=True,
            auth_type="basic", enable_rfc6764=False, rate_limit_handle=False,
        )
        try:
            def check_budget():
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise CalendarSourceError("calendar refresh timed out")
                client.timeout = min(self._config.timeout_seconds, remaining)

            check_budget()
            principal = client.principal()
            check_budget()
            calendars = principal.calendars()
            if (self._config.calendar_id is not None and not any(
                    str(c.url) == self._config.calendar_id for c in calendars)):
                raise CalendarSourceError("configured calendar unavailable")
            events = []
            total_bytes = 0
            component_count = 0
            for calendar in calendars:
                calendar_id = str(calendar.url)
                if self._config.calendar_id is not None and calendar_id != self._config.calendar_id:
                    continue
                combined = Calendar()
                combined.add("version", "2.0")
                combined.add("prodid", "-//SmartScreenOS//CalDAV read-only//EN")
                check_budget()
                # Pad server bounds, then expand complete series locally in the
                # configured timezone (including floating and all-day values).
                resources = self._resources(client, calendar,
                    start - timedelta(days=1), end + timedelta(days=1))
                seen = set()
                for resource in resources:
                    check_budget()
                    data = resource.data
                    if data in seen:
                        continue
                    seen.add(data)
                    size = len(data.encode("utf-8") if isinstance(data, str) else data)
                    total_bytes += size
                    if size > self.MAX_RESOURCE_BYTES or total_bytes > self.MAX_TOTAL_BYTES:
                        raise ValueError("calendar response exceeds size limit")
                    parsed = Calendar.from_ical(data)
                    if parsed.errors:
                        raise ValueError("invalid calendar data")
                    for component in parsed.subcomponents:
                        component_count += 1
                        if component_count > self.MAX_COMPONENTS:
                            raise ValueError("calendar response exceeds component limit")
                        if component.name in ("VEVENT", "VTIMEZONE"):
                            if component.name == "VEVENT":
                                if not str(component.get("UID", "")).strip():
                                    raise ValueError("missing calendar event UID")
                                if component.errors:
                                    raise ValueError("invalid calendar event")
                                # Some cancellation tombstones contain only UID,
                                # RECURRENCE-ID and STATUS. The recurrence library
                                # requires DTSTART even for these non-visible items.
                                if (str(component.get("STATUS", "")).upper() == "CANCELLED"
                                        and "DTSTART" not in component
                                        and "RECURRENCE-ID" in component):
                                    component.add("DTSTART", component.decoded("RECURRENCE-ID"))
                                self._localize_floating(component)
                            combined.add_component(component)
                # Fail the whole refresh on malformed data or one failed calendar;
                # a partial result must never replace a complete cached snapshot.
                for item in self._expand(combined, start, end, check_budget):
                    check_budget()
                    if str(item.get("STATUS", "")).upper() == "CANCELLED":
                        continue
                    raw_start = item.decoded("DTSTART")
                    raw_end = item.decoded("DTEND")
                    event_start, event_end = self._aware(raw_start), self._aware(raw_end)
                    uid = str(item.get("UID", "")).strip()
                    if not uid:
                        raise ValueError("missing calendar event UID")
                    # RFC 5545: DTEND is exclusive; zero-duration events are points.
                    event_start_utc = event_start.astimezone(timezone.utc)
                    event_end_utc = event_end.astimezone(timezone.utc)
                    if not (event_start_utc < end and (event_end_utc > start or
                            event_start_utc == event_end_utc and event_start_utc >= start)):
                        continue
                    events.append(CalendarEventOccurrence(
                        event_id=calendar_id + "#" + uid, calendar_id=calendar_id,
                        title=str(item.get("SUMMARY", "")),
                        start=event_start, end=event_end,
                        all_day=not isinstance(raw_start, datetime),
                    ))
            unique = {(e.calendar_id, e.occurrence_id): e for e in events}
            return tuple(sorted(unique.values(), key=lambda e: (
                e.start.astimezone(timezone.utc), e.end.astimezone(timezone.utc), e.occurrence_id
            )))
        finally:
            client.close()

    def _expand(self, combined, start, end, check_budget):
        # Avoid allocating a full year of dense recurrences in one list.
        query = recurring_ical_events.of(combined)
        cursor = start
        seen = set()
        while cursor < end:
            check_budget()
            stop = min(cursor + timedelta(hours=6), end)
            for item in query.between(cursor.astimezone(self._timezone),
                                      stop.astimezone(self._timezone)):
                check_budget()
                key = (str(item.get("UID", "")), item.decoded("DTSTART").isoformat())
                if key in seen:
                    continue
                seen.add(key)
                if len(seen) > self.MAX_OCCURRENCES:
                    raise ValueError("calendar response exceeds occurrence limit")
                yield item
            cursor = stop

"""CalDAV HTTP facade: bounded single background refresh, never wait for I/O."""
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from threading import Condition, Thread
from time import monotonic
from zoneinfo import ZoneInfo

from .calendar_source import CalendarSourceError, CalendarSyncPending


@dataclass
class _Range:
    start: datetime
    end: datetime
    touched: float
    due: float = 0
    events: tuple | None = None
    fetched_at: float = 0
    last_success: str | None = None
    failed: bool = False


class BackgroundCalendarSource:
    MAX_RANGES = 8
    CACHE_SECONDS = 300
    RETRY_SECONDS = 30
    MAX_STALE_SECONDS = 3600
    IDLE_SECONDS = 900

    def __init__(self, source, *, config, clock=monotonic, now=None, warmup=True):
        self._source, self._config, self._clock = source, config, clock
        self._now = now or (lambda: datetime.now(ZoneInfo('Asia/Shanghai')))
        self._warmup = warmup
        self._warm_key = None
        self._ranges = OrderedDict()
        self._condition = Condition()
        self._thread = None
        self._start_retry_at = 0.0
        self._closed = False
        self._current = None

    def _key(self, start, end):
        zone = ZoneInfo(self._config.timezone)
        def aware(value):
            if value.tzinfo is None:
                value = value.replace(tzinfo=zone)
            return value.astimezone(timezone.utc)
        try:
            start, end = aware(start), aware(end)
            start - timedelta(days=1)
            end + timedelta(days=1)
        except (ValueError, OverflowError):
            raise ValueError('invalid calendar range') from None
        if end < start or end - start > timedelta(days=366):
            raise ValueError('invalid calendar range')
        return start, end

    def _register(self, key):
        if key not in self._ranges:
            if len(self._ranges) >= self.MAX_RANGES:
                victim = next(k for k in self._ranges if k != self._current)
                del self._ranges[victim]
            self._ranges[key] = _Range(*key, touched=self._clock())
        self._ranges.move_to_end(key)
        return self._ranges[key]

    def start(self):
        with self._condition:
            if self._closed:
                return
            if self._thread is None and self._clock() >= self._start_retry_at:
                thread = Thread(target=self._run, daemon=True, name='calendar-background')
                try:
                    thread.start()
                except (RuntimeError, OSError):
                    # A calendar thread/resource failure must not abort household startup.
                    self._start_retry_at = self._clock() + self.RETRY_SECONDS
                else:
                    self._thread = thread

    def stop(self):
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def join(self, timeout=1):
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def snapshot_details(self, start, end):
        key = self._key(start, end)
        if key[0] == key[1]:
            return (), dict(state='fresh', stale=False, age_seconds=0, last_success_at=None)
        self.start()
        # Worker never holds this lock across network/parsing/recurrence work.
        with self._condition:
            if self._closed:
                raise CalendarSyncPending('stopped', 30)
            entry = self._register(key)
            entry.touched = self._clock()
            age = max(0, self._clock() - entry.fetched_at)
            fresh = entry.events is not None and age < self.CACHE_SECONDS
            stale = (not fresh and self._config.allow_stale and entry.events is not None
                     and age < self.MAX_STALE_SECONDS)
            self._condition.notify_all()
            if fresh or stale:
                return entry.events, dict(state='stale' if stale else 'fresh', stale=bool(stale),
                    age_seconds=int(age), last_success_at=entry.last_success)
            due = max(entry.due, self._start_retry_at)
            retry = max(1, min(30, int(due - self._clock()) + 1))
            unavailable = self._thread is None or (entry.failed and self._current != key)
            raise CalendarSyncPending('unavailable' if unavailable else 'syncing', retry)

    def list_events(self, start, end):
        return self.snapshot_details(start, end)[0]

    def snapshot(self, start, end):
        events, status = self.snapshot_details(start, end)
        return events, status['stale']

    def _run(self):
        while True:
            with self._condition:
                if self._closed:
                    return
                now = self._clock()
                if self._warmup:
                    # Match existing iPad query exactly: Shanghai midnight +10 days.
                    today = self._now().astimezone(ZoneInfo('Asia/Shanghai')).date()
                    start = datetime.combine(today, time.min, ZoneInfo('Asia/Shanghai'))
                    warm_key = self._key(start, start + timedelta(days=10))
                    if warm_key != self._warm_key:
                        self._warm_key = warm_key
                        self._register(warm_key)
                for key in list(self._ranges):
                    if key != self._warm_key and now - self._ranges[key].touched > self.IDLE_SECONDS:
                        del self._ranges[key]
                due = [(key, entry) for key, entry in self._ranges.items() if now >= entry.due]
                if not due:
                    self._condition.wait(timeout=1)
                    continue
                # Cold ranges first; at most one refresh and no per-request thread.
                key, entry = min(due, key=lambda item: (item[1].events is not None, item[1].due))
                self._current = key
            try:
                events, status = self._source.snapshot_details(*key)
                if status.get('stale'):
                    raise CalendarSourceError('calendar service unavailable')
                events = tuple(events)
                fetched_at = self._clock() - max(0, int(status.get('age_seconds', 0)))
                success = status.get('last_success_at')
            except Exception:
                with self._condition:
                    self._current = None
                    if self._closed:
                        return
                    entry.failed = True
                    entry.due = self._clock() + self.RETRY_SECONDS
            else:
                with self._condition:
                    self._current = None
                    if self._closed:
                        return
                    entry.events, entry.fetched_at, entry.last_success = events, fetched_at, success
                    entry.failed = False
                    entry.due = fetched_at + self.CACHE_SECONDS
            with self._condition:
                self._condition.notify_all()

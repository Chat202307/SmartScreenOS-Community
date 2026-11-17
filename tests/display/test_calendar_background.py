from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
import json
from threading import Event, Thread
import time
from urllib.parse import urlencode

import pytest

from src.smartscreen_display.calendar_background import BackgroundCalendarSource
from src.smartscreen_display.calendar_config import CalendarConfig
from src.smartscreen_display.calendar_source import CalendarEventService, CalendarSyncPending
from src.smartscreen_display.server import SnapshotApplication, create_http_server

START = datetime(2026, 11, 15, tzinfo=timezone.utc)
END = START + timedelta(days=10)


class ControlledSource:
    def __init__(self):
        self.entered, self.release = Event(), Event()
        self.calls = []
        self.fail = False
    def snapshot_details(self, start, end):
        self.calls.append((start, end))
        self.entered.set()
        assert self.release.wait(5), 'test must release synthetic source'
        if self.fail:
            raise RuntimeError('private-synthetic-upstream-error')
        return (), dict(stale=False, age_seconds=0, last_success_at='2026-11-15T00:00:00Z')


def facade(source, **options):
    return BackgroundCalendarSource(source, config=CalendarConfig(enabled=True, provider='caldav'),
                                    warmup=False, **options)


def ready(background, start=START, end=END):
    until = time.monotonic() + 4
    while time.monotonic() < until:
        try:
            return background.snapshot_details(start, end)
        except CalendarSyncPending:
            with background._condition:
                background._condition.wait(0.01)
    raise AssertionError('background did not publish synthetic result')


def cleanup(background, source):
    background.stop()
    source.release.set()
    background.join(2)


def test_slow_calendar_does_not_hold_http_or_fake_household_controls():
    source = ControlledSource()
    background = facade(source)
    calls = []
    class Dispatcher:
        def execute(self, **kwargs):
            calls.append(kwargs)
            return 'synthetic-only'
    class Host:
        def snapshot(self):
            return {'capabilities': {}}
    app = SnapshotApplication(Host(), calendar_event_service=CalendarEventService(source=background),
                              device_control_dispatcher=Dispatcher())
    server = create_http_server(app, host='127.0.0.1', port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(path, method='GET', body=None):
        connection = HTTPConnection('127.0.0.1', server.server_port, timeout=2)
        try:
            connection.request(method, path, body=body)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            connection.close()
    path = '/api/calendar?' + urlencode(dict(start=START.isoformat(), end=END.isoformat()))
    try:
        began = time.monotonic()
        status, headers, body = request(path)
        assert status == 503 and time.monotonic() - began < 1
        assert headers['Retry-After'] == '1' and body['calendar_status']['state'] == 'syncing'
        assert 'events' not in body
        assert source.entered.wait(2)
        assert request('/api/snapshot')[0] == 200
        assert request('/api/device/actions', 'POST', json.dumps(dict(
            device_id='synthetic-only', control_id='power', value=True)))[0] == 200
        assert len(calls) == 1 and len(source.calls) == 1
        source.release.set()
        ready(background)
        assert request(path)[0] == 200
    finally:
        cleanup(background, source)
        server.shutdown()
        server.server_close()
        thread.join(2)


def test_many_callers_deduplicate_and_bound_pending_ranges():
    source = ControlledSource()
    background = facade(source)
    def pending(index):
        with pytest.raises(CalendarSyncPending):
            background.snapshot_details(START, END)
    try:
        with ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(pending, range(40)))
        assert source.entered.wait(2) and len(source.calls) == 1
        for index in range(20):
            with pytest.raises(CalendarSyncPending):
                background.snapshot_details(START + timedelta(minutes=index+1), END)
        assert len(background._ranges) == 8 and len(source.calls) == 1
    finally:
        cleanup(background, source)


def test_expiry_is_fail_closed_while_automatic_refresh_runs():
    source = ControlledSource()
    clock = [1000.0]
    background = facade(source, clock=lambda: clock[0])
    try:
        source.release.set()
        _, status = ready(background)
        assert status['state'] == 'fresh' and status['age_seconds'] == 0
        source.entered.clear()
        source.release.clear()
        clock[0] += 301
        # Timer gets notified without requiring an HTTP-triggered refresh.
        with background._condition:
            background._condition.notify_all()
        assert source.entered.wait(2)
        with pytest.raises(CalendarSyncPending):
            background.snapshot_details(START, END)
        assert len(source.calls) == 2
        source.release.set()
        _, status = ready(background)
        assert status['last_success_at'] and not status['stale']
    finally:
        cleanup(background, source)


def test_failed_job_retries_after_backoff_without_leaking_private_errors():
    source = ControlledSource()
    source.fail = True
    source.release.set()
    clock = [1000.0]
    background = facade(source, clock=lambda: clock[0])
    try:
        with pytest.raises(CalendarSyncPending):
            background.snapshot_details(START, END)
        assert source.entered.wait(2)
        with background._condition:
            assert background._condition.wait_for(lambda: background._current is None, timeout=2)
        for _ in range(20):
            with pytest.raises(CalendarSyncPending) as error:
                background.snapshot_details(START, END)
            assert error.value.status['state'] == 'unavailable'
            assert 'private' not in str(error.value)
        assert len(source.calls) == 1
        source.fail = False
        clock[0] += 31
        with background._condition:
            background._condition.notify_all()
        ready(background)
        assert len(source.calls) == 2
    finally:
        cleanup(background, source)


def test_startup_prewarms_existing_ipad_range_without_http():
    source = ControlledSource()
    background = BackgroundCalendarSource(source, config=CalendarConfig(enabled=True),
        now=lambda: datetime.fromisoformat('2026-11-15T12:00:00+08:00'))
    try:
        background.start()
        assert source.entered.wait(2)
        assert source.calls == [(datetime.fromisoformat('2026-11-15T00:00:00+08:00'),
                                 datetime.fromisoformat('2026-11-25T00:00:00+08:00'))]
    finally:
        cleanup(background, source)


def test_shutdown_is_bounded_and_late_result_not_published():
    source = ControlledSource()
    background = facade(source)
    with pytest.raises(CalendarSyncPending):
        background.snapshot_details(START, END)
    assert source.entered.wait(2)
    began = time.monotonic()
    background.stop()
    assert time.monotonic() - began < 1
    source.release.set()
    background.join(2)
    assert background._ranges[(START, END)].events is None
    with pytest.raises(CalendarSyncPending) as error:
        background.snapshot_details(START, END)
    assert error.value.status['state'] == 'stopped' and len(source.calls) == 1


@pytest.mark.parametrize('start,end', [(END, START), (START, START+timedelta(days=367)),
                                      (datetime.min, START)])
def test_bad_range_never_starts_background_or_network(start, end):
    source = ControlledSource()
    background = facade(source)
    with pytest.raises(ValueError):
        background.snapshot_details(start, end)
    assert background._thread is None and not source.calls


def test_explicit_stale_opt_in_remains_visible_during_refresh():
    source = ControlledSource()
    clock = [1000.0]
    background = BackgroundCalendarSource(source,
        config=CalendarConfig(enabled=True, allow_stale=True), clock=lambda: clock[0], warmup=False)
    try:
        source.release.set()
        ready(background)
        source.release.clear()
        clock[0] += 301
        _, status = background.snapshot_details(START, END)
        assert status['stale'] is True and status['state'] == 'stale'
        clock[0] += 3600
        with pytest.raises(CalendarSyncPending):
            background.snapshot_details(START, END)
    finally:
        cleanup(background, source)


def test_calendar_thread_exhaustion_does_not_abort_household_startup(monkeypatch):
    import src.smartscreen_display.calendar_background as module
    actual_thread = module.Thread
    class RefusedThread:
        def __init__(self, **kwargs):
            pass
        def start(self):
            raise RuntimeError('synthetic thread capacity exhausted')
    source = ControlledSource()
    clock = [1000.0]
    background = facade(source, clock=lambda: clock[0])
    monkeypatch.setattr(module, 'Thread', RefusedThread)
    background.start()  # Must remain safe for application startup.
    with pytest.raises(CalendarSyncPending) as error:
        background.snapshot_details(START, END)
    assert error.value.status['state'] == 'unavailable' and error.value.retry_after == 30
    assert not source.calls
    monkeypatch.setattr(module, 'Thread', actual_thread)
    clock[0] += 31
    source.release.set()
    try:
        assert ready(background)[1]['state'] == 'fresh'
    finally:
        cleanup(background, source)

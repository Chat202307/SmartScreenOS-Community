from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import json

import pytest

from src.smartscreen_display.calendar_config import CalendarConfig, load_calendar_config
from src.smartscreen_display.calendar_source import CalendarEventService, CalendarSourceError
from src.smartscreen_display.caldav_calendar_source import CalDAVCalendarSource
from src.smartscreen_display.server import SnapshotApplication


def dt(value):
    return datetime.fromisoformat(value)


START = dt("2026-03-01T00:00:00+08:00")
END = dt("2026-04-01T00:00:00+08:00")


def ics(*events):
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + "\r\n".join(events) + "\r\nEND:VCALENDAR\r\n"


def event(lines):
    return "BEGIN:VEVENT\r\n" + lines.replace("\n", "\r\n") + "\r\nEND:VEVENT"


class FakeCalendar:
    def __init__(self, url, data):
        self.url, self.data = url, data
        self.calls = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.data, Exception):
            raise self.data
        return [SimpleNamespace(data=data) for data in self.data]


class FakeClient:
    def __init__(self, calendars):
        self.items = calendars
        self.closed = 0
        self.options = []

    def __call__(self, **kwargs):
        self.options.append(kwargs)
        return self

    def principal(self):
        return self

    def calendars(self):
        return self.items

    def close(self):
        self.closed += 1


@pytest.fixture
def setup_source(tmp_path):
    secret = tmp_path / "app-password"
    secret.write_text("test-only-secret\n")
    clock = [1000.0]
    def make(calendars, **options):
        client = FakeClient(calendars)
        config = CalendarConfig(enabled=True, provider="caldav", **options)
        source = CalDAVCalendarSource(
            config=config, client_factory=client, clock=lambda: clock[0],
            environ={"SMARTSCREEN_ICLOUD_USERNAME": "test@example.invalid",
                     "SMARTSCREEN_ICLOUD_PASSWORD_FILE": str(secret)},
        )
        return source, client, clock
    return make


def simple(uid="same", extra=""):
    return event("UID:" + uid + "\nDTSTART:20260305T020000Z\nDTEND:20260305T030000Z\nSUMMARY:家庭日程" + extra)


def test_discovers_all_calendars_and_namespaces_uids(setup_source):
    calendars = [FakeCalendar("https://example.invalid/one", [ics(simple())]),
                 FakeCalendar("https://example.invalid/two", [ics(simple())])]
    source, client, _ = setup_source(calendars, timeout_seconds=7)
    events = source.list_events(START, END)
    assert len(events) == 2
    assert len({e.event_id for e in events}) == 2
    assert {e.calendar_id for e in events} == {c.url for c in calendars}
    assert client.closed == 1
    assert client.options[0]["timeout"] == 7
    assert client.options[0]["ssl_verify_cert"] is True
    assert client.options[0]["enable_rfc6764"] is False
    assert client.options[0]["rate_limit_handle"] is False
    assert all(c.calls[0]["expand"] is False for c in calendars)


def test_recurrence_exdate_rdate_moved_and_cancelled_overrides(setup_source):
    master = event("UID:series\nDTSTART;TZID=Asia/Shanghai:20260301T090000\nDTEND;TZID=Asia/Shanghai:20260301T100000\nRRULE:FREQ=DAILY;COUNT=5\nEXDATE;TZID=Asia/Shanghai:20260302T090000\nRDATE;TZID=Asia/Shanghai:20260309T090000\nSUMMARY:Original")
    moved = event("UID:series\nRECURRENCE-ID;TZID=Asia/Shanghai:20260303T090000\nDTSTART;TZID=Asia/Shanghai:20260303T140000\nDTEND;TZID=Asia/Shanghai:20260303T150000\nSUMMARY:Moved")
    cancelled = event("UID:series\nRECURRENCE-ID;TZID=Asia/Shanghai:20260304T090000\nDTSTART;TZID=Asia/Shanghai:20260304T090000\nDTEND;TZID=Asia/Shanghai:20260304T100000\nSTATUS:CANCELLED")
    calendar = FakeCalendar("cal-1", [ics(master, moved, cancelled)])
    source, _, _ = setup_source([calendar])
    events = source.list_events(START, END)
    assert [(e.start.day, e.start.hour) for e in events] == [(1, 9), (3, 14), (5, 9), (9, 9)]
    assert events[1].title == "Moved"
    assert len({e.occurrence_id for e in events}) == 4


def test_all_day_exclusive_end_duration_missing_end_and_floating(setup_source):
    data = ics(event("UID:all\nDTSTART;VALUE=DATE:20260305\nDTEND;VALUE=DATE:20260307\nRRULE:FREQ=WEEKLY;COUNT=2"),
               event("UID:one-day\nDTSTART;VALUE=DATE:20260308"),
               event("UID:floating\nDTSTART:20260305T090000\nDURATION:PT90M"),
               event("UID:point\nDTSTART:20260306T090000"))
    source, _, _ = setup_source([FakeCalendar("cal", [data])])
    events = source.list_events(START, END)
    all_day = [e for e in events if e.event_id.endswith("#all")]
    assert len(all_day) == 2
    assert all(e.all_day and e.end - e.start == timedelta(days=2) for e in all_day)
    assert all_day[0].start.isoformat() == "2026-03-05T00:00:00+08:00"
    assert next(e for e in events if e.event_id.endswith("#one-day")).end.day == 9
    floating = next(e for e in events if e.event_id.endswith("#floating"))
    assert floating.start.isoformat() == "2026-03-05T09:00:00+08:00"
    assert floating.end - floating.start == timedelta(minutes=90)
    point = next(e for e in events if e.event_id.endswith("#point"))
    assert point.start == point.end
    assert not source.list_events(dt("2026-03-07T00:00:00+08:00"), dt("2026-03-08T00:00:00+08:00"))


def test_timezone_dst_recurrence(setup_source):
    data = ics(event("UID:dst\nDTSTART;TZID=America/New_York:20260307T090000\nDTEND;TZID=America/New_York:20260307T100000\nRRULE:FREQ=DAILY;COUNT=3"))
    source, _, _ = setup_source([FakeCalendar("cal", [data])])
    events = source.list_events(START, END)
    assert [e.start.hour for e in events] == [9, 9, 9]
    assert [e.start.utcoffset() for e in events] == [timedelta(hours=-5), timedelta(hours=-4), timedelta(hours=-4)]


def test_this_and_future_override_and_cancelled_series(setup_source):
    master = event("UID:series\nDTSTART:20260301T090000Z\nDTEND:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=4")
    changed = event("UID:series\nRECURRENCE-ID;RANGE=THISANDFUTURE:20260302T090000Z\nDTSTART:20260302T110000Z\nDTEND:20260302T120000Z\nSUMMARY:Later")
    cancelled = event("UID:cancelled\nDTSTART:20260301T090000Z\nDTEND:20260301T100000Z\nRRULE:FREQ=DAILY;COUNT=3\nSTATUS:CANCELLED")
    source, _, _ = setup_source([FakeCalendar("cal", [ics(master, changed, cancelled)])])
    events = source.list_events(START, END)
    assert [(e.start.day, e.start.hour) for e in events] == [(1, 9), (2, 11), (3, 11), (4, 11)]


def test_moved_occurrence_enters_query_and_overnight_overlap(setup_source):
    master = event("UID:series\nDTSTART:20260201T090000Z\nDTEND:20260201T100000Z\nRRULE:FREQ=DAILY;COUNT=2")
    moved = event("UID:series\nRECURRENCE-ID:20260202T090000Z\nDTSTART:20260302T090000Z\nDTEND:20260302T100000Z")
    overnight = event("UID:overnight\nDTSTART:20260228T150000Z\nDTEND:20260228T170000Z")
    source, _, _ = setup_source([FakeCalendar("cal", [ics(master, moved, overnight)])])
    events = source.list_events(START, END)
    assert len(events) == 2
    assert events[0].event_id.endswith("#overnight")
    assert events[1].start.day == 2


def test_embedded_vtimezone(setup_source):
    custom = "BEGIN:VTIMEZONE\r\nTZID:Custom/Office\r\nBEGIN:STANDARD\r\nDTSTART:19700101T000000\r\nTZOFFSETFROM:+0530\r\nTZOFFSETTO:+0530\r\nEND:STANDARD\r\nEND:VTIMEZONE"
    data = ics(custom, event("UID:custom\nDTSTART;TZID=Custom/Office:20260301T090000\nDTEND;TZID=Custom/Office:20260301T100000\nRRULE:FREQ=DAILY;COUNT=2"))
    source, _, _ = setup_source([FakeCalendar("cal", [data])])
    events = source.list_events(START, END)
    assert len(events) == 2
    assert all(e.start.utcoffset() == timedelta(hours=5, minutes=30) for e in events)


def test_cache_expiry_retry_stale_limit_and_recovery(setup_source, caplog):
    calendar = FakeCalendar("cal", [ics(simple())])
    source, client, clock = setup_source([calendar], allow_stale=True)
    first, stale = source.snapshot(START, END)
    assert not stale
    clock[0] += 299
    assert source.list_events(START, END) == first
    assert len(client.options) == 1
    clock[0] += 1
    calendar.data = TimeoutError("test-only-secret test@example.invalid")
    assert source.snapshot(START, END) == (first, True)
    assert "test-only-secret" not in caplog.text
    assert len(client.options) == 2
    clock[0] += 29
    assert source.snapshot(START, END) == (first, True)
    assert len(client.options) == 2
    with pytest.raises(CalendarSourceError):
        source.list_events(START + timedelta(days=1), END)
    clock[0] += 1
    calendar.data = [ics(simple("changed"))]
    assert source.snapshot(START, END)[0][0].event_id.endswith("#changed")
    clock[0] += 3600
    calendar.data = RuntimeError("private response")
    with pytest.raises(CalendarSourceError, match="calendar service unavailable") as exc:
        source.snapshot(START, END)
    assert exc.value.__cause__ is None
    assert "private response" not in str(exc.value)
    assert client.closed == len(client.options)


def test_partial_failure_does_not_replace_complete_cache(setup_source):
    one, two = FakeCalendar("one", [ics(simple())]), FakeCalendar("two", [ics(simple())])
    source, _, clock = setup_source([one, two], allow_stale=True)
    events = source.list_events(START, END)
    clock[0] += 300
    one.data = []
    two.data = RuntimeError("offline")
    assert source.snapshot(START, END) == (events, True)


def test_empty_results_cached_and_removed_events_disappear(setup_source):
    calendar = FakeCalendar("cal", [ics(simple())])
    source, client, clock = setup_source([calendar])
    assert source.list_events(START, END)
    clock[0] += 300
    calendar.data = []
    assert source.list_events(START, END) == ()
    assert source.list_events(START, END) == ()
    assert len(client.options) == 2


def test_cache_bound_concurrency_and_duplicate_resources(setup_source):
    data = ics(simple())
    source, client, _ = setup_source([FakeCalendar("cal", [data, data])])
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: source.list_events(START, END), range(5)))
    assert all(len(r) == 1 for r in results)
    assert len(client.options) == 1
    for day in range(10):
        source.list_events(START + timedelta(days=day), END)
    assert len(source._cache) == 8


def test_calendar_filter_and_range_validation(setup_source):
    one, two = FakeCalendar("one", [ics(simple())]), FakeCalendar("two", [ics(simple())])
    source, client, _ = setup_source([one, two], calendar_id="two")
    assert len(source.list_events(START, END)) == 1
    assert not one.calls
    assert source.list_events(START, START) == ()
    for start, end in [(END, START), (START, START + timedelta(days=367))]:
        with pytest.raises(ValueError):
            source.list_events(start, end)
    assert len(client.options) == 1


def test_missing_credentials_and_malformed_data_are_sanitized(setup_source):
    source, client, clock = setup_source([FakeCalendar("cal", ["broken ICS"])])
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)
    assert client.closed == 1
    clock[0] += 30
    source._environ = {}
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)
    assert len(client.options) == 1


def test_http_failure_and_stale_headers(setup_source):
    calendar = FakeCalendar("cal", [ics(simple())])
    source, _, clock = setup_source([calendar], allow_stale=True)
    app = SnapshotApplication(SimpleNamespace(snapshot=lambda: {}),
                              calendar_event_service=CalendarEventService(source=source))
    path = "/api/calendar?start=2026-03-01T00:00:00%2B08:00&end=2026-04-01T00:00:00%2B08:00"
    status, headers, body = app.handle(method="GET", path=path)
    assert status == 200 and "X-Calendar-Stale" not in headers
    clock[0] += 300
    calendar.data = TimeoutError("secret")
    status, headers, stale_body = app.handle(method="GET", path=path)
    assert status == 200 and headers["X-Calendar-Stale"] == "true"
    assert json.loads(body)["events"] == json.loads(stale_body)["events"]
    assert headers["Cache-Control"] == "no-store"
    details = json.loads(stale_body)["calendar_status"]
    assert details["state"] == "stale" and details["stale"] is True
    assert details["age_seconds"] == 300
    assert details["last_success_at"] == json.loads(body)["calendar_status"]["last_success_at"]
    clock[0] += 3600
    status, _, body = app.handle(method="GET", path=path)
    assert status == 503
    assert json.loads(body) == {"error": "calendar service unavailable"}


@pytest.mark.parametrize("patch", [
    {"url": "http://example.invalid"}, {"url": "https://user:secret@example.invalid"},
    {"url": "https://example.invalid/?password=secret"}, {"url": None},
    {"timezone": "bad/timezone"}, {"timezone": None},
    {"timeout_seconds": 0}, {"timeout_seconds": True}, {"timeout_seconds": float("inf")},
    {"timeout_seconds": 61}, {"username_env": ""}, {"password_file_env": "a=b"},
    {"password": "secret"}, {"app_password": "secret"}, {"username": "private"},
])
def test_config_rejects_unsafe_or_invalid_caldav_settings(tmp_path, patch):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"enabled": True, "provider": "caldav", **patch}))
    with pytest.raises(ValueError):
        load_calendar_config(path)


def test_config_defaults_all_calendars(tmp_path):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"enabled": True, "provider": "caldav"}))
    config = load_calendar_config(path)
    assert config.calendar_id is None
    assert config.url == "https://caldav.icloud.com/"
    assert config.timeout_seconds == 30
    assert config.timezone == "Asia/Shanghai"
    assert config.allow_stale is False
    assert config.refresh_timeout_seconds == 120


@pytest.mark.parametrize("query", [
    "start=2026-03-01T00:00:00&end=2026-03-02T00:00:00Z",
    "start=2026-03-01T00:00:00Z&end=2028-03-02T00:00:00Z",
])
def test_http_invalid_ranges_do_not_contact_upstream(setup_source, query):
    source, client, _ = setup_source([])
    app = SnapshotApplication(SimpleNamespace(snapshot=lambda: {}),
                              calendar_event_service=CalendarEventService(source=source))
    assert app.handle(method="GET", path="/api/calendar?" + query)[0] == 400
    assert not client.options


@pytest.mark.parametrize("data,start,end", [
    (ics(simple()), START, END),
    (ics(event("UID:all\nDTSTART;VALUE=DATE:20260305\nDTEND;VALUE=DATE:20260306")),
     dt("2026-03-05T00:00:00+08:00"), dt("2026-03-05T01:00:00+08:00")),
    (ics(event("UID:floating\nDTSTART:20260305T003000\nDTEND:20260305T004500")),
     dt("2026-03-05T00:00:00+08:00"), dt("2026-03-05T01:00:00+08:00")),
])
def test_real_davclient_discovers_principal_home_and_queries_all_calendars(tmp_path, monkeypatch, data, start, end):
    """Exercise actual caldav discovery, XML REPORT generation and XML parsing.

    Only the HTTP transport is replaced; no Apple account or external network.
    """
    import niquests
    from xml.sax.saxutils import escape

    calls = []
    base = "https://caldav.example.invalid"
    def response(href, props):
        return f"<d:response><d:href>{href}</d:href><d:propstat><d:prop>{props}</d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>"
    def request(session, method, url, **kwargs):
        calls.append((method, url, kwargs))
        assert kwargs["timeout"] == 30
        assert kwargs["verify"] is True
        assert method in ("PROPFIND", "REPORT")
        if method == "REPORT":
            assert b"time-range" in kwargs["data"]
            assert b"expand" not in kwargs["data"]
            from xml.etree import ElementTree
            node = ElementTree.fromstring(kwargs["data"]).find(".//{urn:ietf:params:xml:ns:caldav}time-range")
            assert node.get("start") == (start - timedelta(days=1)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            body = response(url + "event.ics", "<c:calendar-data>" + escape(data) + "</c:calendar-data>")
        elif url.rstrip("/") == base:
            body = response("/", "<d:current-user-principal><d:href>/principal/</d:href></d:current-user-principal>")
        elif "/principal" in url:
            body = response("/principal/", "<c:calendar-home-set><d:href>/home/</d:href></c:calendar-home-set>")
        elif url.rstrip("/") == base + "/home":
            props = '<d:resourcetype><d:collection/><c:calendar/></d:resourcetype><d:displayname>Test</d:displayname><c:supported-calendar-component-set><c:comp name="VEVENT"/></c:supported-calendar-component-set>'
            body = response("/home/one/", props) + response("/home/two/", props)
        else:
            raise AssertionError(url)
        xml = '<d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">' + body + '</d:multistatus>'
        result = niquests.Response()
        result.status_code = 207
        result._content = xml.encode()
        result.headers["Content-Type"] = "application/xml"
        return result

    monkeypatch.setattr(niquests.Session, "request", request)
    secret = tmp_path / "password"
    secret.write_text("test-only-secret")
    source = CalDAVCalendarSource(
        config=CalendarConfig(enabled=True, provider="caldav", url=base + "/"),
        environ={"SMARTSCREEN_ICLOUD_USERNAME": "test@example.invalid",
                 "SMARTSCREEN_ICLOUD_PASSWORD_FILE": str(secret)},
    )
    events = source.list_events(start, end)
    assert len(events) == 2
    assert {e.calendar_id for e in events} == {base + "/home/one/", base + "/home/two/"}
    assert len([c for c in calls if c[0] == "REPORT"]) == 2


def test_expired_cache_fails_closed_by_default(setup_source):
    calendar = FakeCalendar("cal", [ics(simple())])
    source, _, clock = setup_source([calendar])
    source.list_events(START, END)
    clock[0] += 300
    calendar.data = TimeoutError("offline")
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)
    assert source._cache  # retained for recovery, never relabelled as fresh


def test_total_deadline_quarantines_late_result_and_limits_workers(setup_source):
    from threading import Event
    from time import monotonic
    source, _, clock = setup_source([], refresh_timeout_seconds=0.05)
    release, entered = Event(), Event()
    calls = []
    original_fetch = source._fetch
    def blocked_fetch(start, end):
        calls.append(1)
        entered.set()
        release.wait(timeout=3)
        return ()
    source._fetch = blocked_fetch
    try:
        began = monotonic()
        with pytest.raises(CalendarSourceError):
            source.snapshot(START, END)
        assert monotonic() - began < 2
        assert entered.is_set()
        task = source._pending
        clock[0] += 30
        with pytest.raises(CalendarSourceError):
            source.snapshot(START, END)
        assert source._pending is task and len(calls) == 1
        release.set()
        assert task.done.wait(timeout=2)
        assert not source._cache
        source._fetch = original_fetch
        clock[0] += 30
        assert source.snapshot(START, END) == ((), False)
    finally:
        release.set()


def test_lock_wait_has_deadline(setup_source):
    source, client, _ = setup_source([], refresh_timeout_seconds=0.02)
    source._lock.acquire()
    try:
        with pytest.raises(CalendarSourceError):
            source.list_events(START, END)
        assert not client.options
    finally:
        source._lock.release()


@pytest.mark.parametrize("patch", [
    {"refresh_timeout_seconds": True}, {"refresh_timeout_seconds": 0},
    {"refresh_timeout_seconds": 121}, {"refresh_timeout_seconds": float("nan")},
    {"allow_stale": "true"},
])
def test_review_config_invalid_options(tmp_path, patch):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"enabled": True, "provider": "caldav", **patch}))
    with pytest.raises(ValueError):
        load_calendar_config(path)


def test_missing_selected_calendar_and_unknown_timezone_fail_closed(setup_source):
    source, _, _ = setup_source([], calendar_id="missing")
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)
    data = ics(event("UID:bad\nDTSTART;TZID=Unknown/Unresolvable:20260305T090000\nDTEND;TZID=Unknown/Unresolvable:20260305T100000"))
    source, _, _ = setup_source([FakeCalendar("cal", [data])])
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)


def test_bad_uid_size_and_recurrence_limits_preserve_failure(setup_source):
    source, _, _ = setup_source([FakeCalendar("cal", [ics(event("DTSTART:20260305T090000Z"))])])
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)
    source, _, _ = setup_source([FakeCalendar("cal", [ics(simple())])])
    source.MAX_RESOURCE_BYTES = 10
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)
    source, _, _ = setup_source([FakeCalendar("cal", [ics(event("UID:dense\nDTSTART:20260305T090000Z\nRRULE:FREQ=HOURLY;COUNT=6"))])])
    source.MAX_OCCURRENCES = 3
    with pytest.raises(CalendarSourceError):
        source.list_events(START, END)


def test_dst_fold_order_and_duration_are_compared_as_instants():
    from zoneinfo import ZoneInfo
    from src.smartscreen_display.calendar_source import CalendarEventOccurrence
    zone = ZoneInfo("America/New_York")
    first = datetime(2026, 11, 1, 1, 45, tzinfo=zone, fold=0)
    later = datetime(2026, 11, 1, 1, 15, tzinfo=zone, fold=1)
    event_one = CalendarEventOccurrence("one", "cal", "early", first, later, False)
    event_two = CalendarEventOccurrence("two", "cal", "later", later, later, False)
    service = CalendarEventService(source=SimpleNamespace(list_events=lambda *_: (event_two, event_one)))
    assert service.list_events(start=START, end=END) == (event_one, event_two)
    with pytest.raises(ValueError):
        CalendarEventOccurrence("bad", "cal", "backwards", later, first, False)


@pytest.mark.parametrize("start,end", [
    ("0001-01-01T00:00:00+14:00", "0001-01-02T00:00:00+14:00"),
    ("9999-12-30T00:00:00Z", "9999-12-31T23:59:59Z"),
])
def test_extreme_dates_are_invalid_ranges_not_upstream_failures(setup_source, start, end):
    source, client, _ = setup_source([])
    with pytest.raises(ValueError):
        source.list_events(dt(start), dt(end))
    assert not client.options


def test_floating_until_and_minimal_cancellation_tombstone(setup_source):
    data = ics(
        event("UID:float\nDTSTART:20260301T090000\nDTEND:20260301T100000\nRRULE:FREQ=DAILY;UNTIL=20260303T090000"),
        event("UID:float\nRECURRENCE-ID:20260302T090000\nSTATUS:CANCELLED"),
    )
    source, _, _ = setup_source([FakeCalendar("cal", [data])])
    events = source.list_events(START, END)
    assert [e.start.isoformat() for e in events] == [
        "2026-03-01T09:00:00+08:00", "2026-03-03T09:00:00+08:00",
    ]


def test_file_username_reference_hides_account_from_docker_environment(tmp_path):
    username, password = tmp_path / 'username', tmp_path / 'password'
    username.write_text('synthetic@example.invalid\n')
    password.write_text('synthetic-app-password\n')
    config = CalendarConfig(enabled=True, provider='caldav', username_file_env='TEST_USERNAME_FILE')
    client = FakeClient([])
    source = CalDAVCalendarSource(config=config, client_factory=client, environ={
        'TEST_USERNAME_FILE': str(username), config.password_file_env: str(password),
        config.username_env: 'must-not-be-used'})
    assert source.list_events(START, END) == ()
    assert client.options[0]['username'] == 'synthetic@example.invalid'
    assert client.options[0]['password'] == 'synthetic-app-password'
    # Explicit file mode must not fall back to a different identity.
    broken = CalDAVCalendarSource(config=config, client_factory=client,
                                 environ={config.username_env: 'synthetic-fallback'})
    with pytest.raises(CalendarSourceError):
        broken.list_events(START, END)
    assert len(client.options) == 1


@pytest.mark.parametrize('value', ['', False, 'invalid reference', 'account@example.invalid'])
def test_username_file_reference_rejects_values_and_invalid_names(tmp_path, value):
    path = tmp_path / 'calendar.json'
    path.write_text(json.dumps(dict(enabled=True, provider='caldav', username_file_env=value)))
    with pytest.raises(ValueError):
        load_calendar_config(path)

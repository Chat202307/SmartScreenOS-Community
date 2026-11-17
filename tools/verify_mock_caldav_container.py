#!/usr/bin/env python3
"""Execute only in the synthetic internal Docker network; output summary only."""
from datetime import datetime, timedelta
import errno
from http.client import HTTPConnection, HTTPSConnection
import json
import os
from pathlib import Path
import runpy
import ssl
import time
from urllib.parse import urlencode


CA = "/test/ca.pem"


def probe(path, method="GET", *, host="calendar-probe"):
    connection = HTTPConnection(host, 19081, timeout=15)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        raw = response.read()
        return response.status, dict(response.getheaders()), json.loads(raw)
    finally:
        connection.close()


def mock(path, *, mode=None):
    connection = HTTPSConnection("mock-caldav", 8443, timeout=5,
                                 context=ssl.create_default_context(cafile=CA))
    try:
        body = json.dumps({"mode": mode}) if mode else None
        connection.request("POST" if mode else "GET", path, body=body,
                           headers={"Content-Type": "application/json"} if mode else {})
        response = connection.getresponse()
        data = json.loads(response.read())
        assert response.status == 200, "mock control endpoint failed"
        return data
    finally:
        connection.close()


def query(start="2026-10-30T00:00:00+08:00", end="2026-11-10T00:00:00+08:00"):
    return "/api/calendar?" + urlencode({"start": start, "end": end})


def main():
    deadline = time.monotonic() + 30
    while True:
        try:
            status, _, health = probe("/health")
            mock("/_lab/stats")
            assert status == 200 and health["mode"] == "synthetic-fixture"
            break
        except (OSError, AssertionError):
            if time.monotonic() >= deadline:
                raise AssertionError("synthetic services did not become ready") from None
            time.sleep(0.25)

    status, headers, payload = probe(query())
    assert status == 200, "initial CalDAV request failed"
    events = payload["events"]
    assert len(events) == 9 and len({item["calendar_id"] for item in events}) == 2
    one = [item for item in events if "/one/" in item["calendar_id"]]
    recurring = [item for item in one if item["event_id"].endswith("#recurring")]
    assert [item["start"] for item in recurring] == ["2026-11-01T09:00:00+08:00", "2026-11-03T14:00:00+08:00"]
    assert len({item["event_id"] for item in events if item["event_id"].endswith("#recurring")}) == 2
    all_day = next(item for item in one if item["all_day"])
    assert all_day["start"] == "2026-11-03T00:00:00+08:00"
    assert datetime.fromisoformat(all_day["end"]) - datetime.fromisoformat(all_day["start"]) == timedelta(days=2)
    dst = [item["start"] for item in one if item["event_id"].endswith("#dst")]
    assert dst == ["2026-10-31T09:00:00-04:00", "2026-11-01T09:00:00-05:00", "2026-11-02T09:00:00-05:00"]
    assert next(item["start"] for item in one if item["event_id"].endswith("#utc")) == "2026-11-02T12:00:00+00:00"
    assert next(item["start"] for item in one if item["event_id"].endswith("#floating")) == "2026-11-03T17:30:00+08:00"
    assert payload["calendar_status"]["state"] == "fresh" and headers["Cache-Control"] == "no-store"
    stats = mock("/_lab/stats")
    assert stats["report"] == 2
    status, _, second = probe(query())
    assert status == 200 and second["events"] == events
    assert second["calendar_status"]["last_success_at"] == payload["calendar_status"]["last_success_at"]
    assert mock("/_lab/stats")["report"] == stats["report"], "cache hit performed a REPORT"

    status, _, midnight = probe(query("2026-11-03T00:00:00+08:00", "2026-11-03T01:00:00+08:00"))
    assert status == 200 and len(midnight["events"]) == 1 and midnight["events"][0]["all_day"]
    for method, path, expected in (("POST", "/api/calendar", 405), ("DELETE", "/api/todos", 405),
                                    ("POST", "/api/device/control", 405), ("GET", "/api/devices", 404)):
        assert probe(path, method)[0] == expected
    before_invalid = mock("/_lab/stats")["report"]
    assert probe(query("2026-11-10T00:00:00+08:00", "2026-10-30T00:00:00+08:00"))[0] == 400
    assert mock("/_lab/stats")["report"] == before_invalid

    mock("/_lab/scenario", mode="timeout")
    failed_range = query("2026-10-29T00:00:00+08:00")
    began = time.monotonic()
    status, _, failure = probe(failed_range)
    timeout_elapsed = time.monotonic() - began
    assert status == 503 and failure == {"error": "calendar service unavailable"}
    assert timeout_elapsed < 15, "mock timeout response exceeded bounded caller budget"
    reports_after_timeout = mock("/_lab/stats")["report"]
    assert probe(failed_range)[0] == 503
    assert mock("/_lab/stats")["report"] == reports_after_timeout, "retry backoff was not respected"
    assert probe(query())[0] == 200, "another failed range replaced a valid cached snapshot"
    mock("/_lab/scenario", mode="normal")
    time.sleep(31)  # Actual production backoff constant, not a patched clock.
    status, _, recovered = probe(failed_range)
    assert status == 200 and len(recovered["events"]) == 9

    mock("/_lab/scenario", mode="malformed")
    status, _, failure = probe(query("2026-10-28T00:00:00+08:00"))
    assert status == 503 and "events" not in failure, "partial calendar results leaked through"
    assert mock("/_lab/stats")["calendar_writes"] == 0

    mock("/_lab/scenario", mode="slow")
    began = time.monotonic()
    status, async_headers, pending = probe(query(), host="calendar-background")
    cold_elapsed = time.monotonic() - began
    assert status == 503 and cold_elapsed < 0.5
    assert pending["calendar_status"]["state"] == "syncing" and "events" not in pending
    assert async_headers["Retry-After"] == "1"
    assert probe("/health", host="calendar-background")[0] == 200
    assert probe("/api/devices", host="calendar-background")[0] == 404
    assert probe("/api/device/actions", "POST", host="calendar-background")[0] == 405
    until = time.monotonic() + 15
    while True:
        status, _, async_result = probe(query(), host="calendar-background")
        if status == 200:
            break
        assert status == 503 and time.monotonic() < until
        time.sleep(0.05)
    assert len(async_result["events"]) == 9 and async_result["calendar_status"]["state"] == "fresh"
    before_cached = mock("/_lab/stats")["report"]
    assert probe(query(), host="calendar-background")[0] == 200
    assert mock("/_lab/stats")["report"] == before_cached
    assert mock("/_lab/stats")["calendar_writes"] == 0

    assert os.getuid() == os.geteuid() == 10001 and os.getgid() == 10001
    assert os.statvfs("/app").f_flag & os.ST_RDONLY
    assert os.statvfs("/test/readable.json").f_flag & os.ST_RDONLY
    assert Path("/test/readable.json").read_text() == '{"synthetic":true}'
    try:
        Path("/test/readable.json").write_text("must not write")
        raise AssertionError("read-only config was writable")
    except OSError as error:
        assert error.errno in (errno.EROFS, errno.EACCES)
    try:
        Path("/test/restricted.json").read_bytes()
        raise AssertionError("UID 10001 read an unauthorized fixture")
    except PermissionError:
        pass
    permission = runpy.run_path("/test/check_lab_permissions.py")
    assert permission["check"]("/test-data", write_probe=True)

    print(json.dumps({
        "result": "passed", "background_cold_response_seconds": round(cold_elapsed, 4),
        "background_pending_then_fresh": "passed", "background_cache_and_health": "passed",
        "synthetic_event_count": 9, "calendar_count": 2,
        "recurrence_exdate_override_cancel": "passed", "all_day_midnight_exclusive_end": "passed",
        "utc_floating_dst": "passed", "cache_hit_no_report": "passed",
        "cache_expiry_300s": "covered by image-contained controlled-clock unit tests, not wall-clock wait",
        "timeout_seconds_observed": round(timeout_elapsed, 3), "backoff_and_recovery": "passed",
        "partial_failure_and_write_routes": "passed", "uid_gid": "10001:10001",
        "readonly_root_config_and_restricted_file": "passed", "tmpfs_read_write": "passed",
        "calendar_mutations": 0, "real_credentials": False,
    }))


if __name__ == "__main__":
    main()

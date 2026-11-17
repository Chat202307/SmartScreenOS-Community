"""Standalone calendar probe. Never bootstrap household runtime or controllers."""
from __future__ import annotations

import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

from .calendar_source import CalendarEventOccurrence, CalendarEventService
from .server import SnapshotApplication

PROXY = "http://egress-proxy:3128"


def secret_text(path: Path) -> str:
    with path.open("rb") as stream:
        value = stream.read(4097)
    if len(value) > 4096 or not value.strip():
        raise ValueError("invalid lab secret file")
    return value.decode("utf-8").strip()


def isolated_environment(environ, *, live):
    # Refuse household credentials/config even if somebody accidentally adds an
    # env_file to the lab deployment. Do not echo names, values or account IDs.
    if any(key.startswith("SMARTSCREEN_") for key in environ):
        raise ValueError("household environment is not allowed in the calendar lab")
    if any(environ.get(key) for key in ("http_proxy", "https_proxy", "no_proxy", "all_proxy")):
        raise ValueError("ambiguous proxy environment is not allowed")
    if live and (environ.get("HTTPS_PROXY") != PROXY or environ.get("HTTP_PROXY") != PROXY
                 or environ.get("NO_PROXY", "") or environ.get("ALL_PROXY", "")):
        raise ValueError("live lab requires the restricted egress proxy")


def fixture_service(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    events = tuple(CalendarEventOccurrence(
        event_id=item["event_id"], calendar_id=item["calendar_id"], title=item["title"],
        start=datetime.fromisoformat(item["start"]), end=datetime.fromisoformat(item["end"]),
        all_day=item["all_day"],
    ) for item in payload["events"])
    if any(event.start.tzinfo is None or event.end.tzinfo is None for event in events):
        raise ValueError("fixture dates must include a timezone")
    def list_events(start, end):
        return tuple(event for event in events if event.start < end and event.end > start)
    return CalendarEventService(source=SimpleNamespace(list_events=list_events))


def live_service(config_path, username_file, password_file, environ):
    isolated_environment(environ, live=True)
    from .calendar_config import load_calendar_config
    from .caldav_calendar_source import CalDAVCalendarSource
    config = load_calendar_config(Path(config_path))
    if not config.enabled or config.provider != "caldav" or config.allow_stale:
        raise ValueError("live lab requires enabled CalDAV with stale fallback disabled")
    from .calendar_test_proxy import destination
    target = urlsplit(config.url)
    destination(f"{target.hostname}:{target.port or 443}")
    # Credentials exist only in this source's private mapping, never Docker ENV.
    credentials = {
        config.username_env: secret_text(Path(username_file)),
        config.password_file_env: str(password_file),
    }
    secret_text(Path(password_file))  # Fail before listening when permissions are wrong.
    return CalendarEventService(source=CalDAVCalendarSource(config=config, environ=credentials),
                                calendar_id=config.calendar_id)


def mock_service(ca_file, password_file, environ):
    """Explicit synthetic mode: fixed internal endpoint and fixed fake credentials."""
    isolated_environment(environ, live=False)
    if ca_file is None or password_file is None:
        raise ValueError("mock fixtures are required")
    if any(environ.get(key) for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")) or environ.get("NO_PROXY") != "*":
        raise ValueError("mock mode requires direct internal-network connections")
    if secret_text(Path(password_file)) != "fixture-password" or not Path(ca_file).is_file():
        raise ValueError("mock mode requires synthetic fixtures")
    import caldav
    from .calendar_config import CalendarConfig
    from .caldav_calendar_source import CalDAVCalendarSource
    config = CalendarConfig(enabled=True, provider="caldav", url="https://mock-caldav:8443/",
                            timeout_seconds=2, refresh_timeout_seconds=10)
    def client_factory(**options):
        # Trust only this generated test CA. Never disable certificate validation.
        return caldav.DAVClient(**dict(options, ssl_verify_cert=str(ca_file)))
    return CalendarEventService(source=CalDAVCalendarSource(
        config=config, client_factory=client_factory,
        environ={config.username_env: "fixture-user", config.password_file_env: str(password_file)},
    ))


class CalendarProbe:
    def __init__(self, service, *, live=False):
        self._calendar = SnapshotApplication(SimpleNamespace(snapshot=lambda: {}),
                                             calendar_event_service=service)
        self._mode = "icloud-read-only" if live else "synthetic-fixture"

    def handle(self, method, path):
        headers = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
        if method != "GET":
            return 405, dict(headers, Allow="GET"), b'{"error":"read only"}'
        route = urlsplit(path).path
        if route == "/health":
            # This checks the probe process, not iCloud authentication/freshness.
            return 200, headers, json.dumps({"probe": "ready", "mode": self._mode}).encode()
        if route == "/api/calendar":
            return self._calendar.handle(method="GET", path=path)
        return 404, headers, b'{"error":"not found"}'


def create_probe_server(probe, host="127.0.0.1", port=8080):
    class Handler(BaseHTTPRequestHandler):
        def respond(self):
            try:
                status, headers, body = probe.handle(self.command, self.path)
            except Exception:
                status, headers, body = 503, {"Cache-Control": "no-store"}, b'{"error":"probe unavailable"}'
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        do_GET = respond
        do_POST = respond
        do_PUT = respond
        do_PATCH = respond
        do_DELETE = respond
        do_OPTIONS = respond
        def log_message(self, *args):
            pass  # Never log URLs, diary entries or upstream response bodies.
    return ThreadingHTTPServer((host, port), Handler)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", type=Path)
    mode.add_argument("--calendar-config-file", type=Path)
    mode.add_argument("--mock-caldav", action="store_true")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--mock-ca-file", type=Path)
    parser.add_argument("--mock-password-file", type=Path)
    parser.add_argument("--icloud-username-file", type=Path, default=Path("/run/secrets/icloud_username"))
    parser.add_argument("--icloud-password-file", type=Path, default=Path("/run/secrets/icloud_app_password"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)
    isolated_environment(os.environ, live=bool(args.calendar_config_file))
    if args.mock_caldav:
        service = mock_service(args.mock_ca_file, args.mock_password_file, os.environ)
    elif args.fixture:
        service = fixture_service(args.fixture)
    else:
        service = live_service(args.calendar_config_file, args.icloud_username_file, args.icloud_password_file, os.environ)
    background = None
    if args.background:
        if args.fixture:
            raise ValueError('background probe requires a CalDAV source')
        from .calendar_background import BackgroundCalendarSource
        raw = service._source
        background = BackgroundCalendarSource(raw, config=raw._config, warmup=False)
        service = CalendarEventService(source=background, calendar_id=raw._config.calendar_id)
        background.start()
    try:
        with create_probe_server(CalendarProbe(service, live=bool(args.calendar_config_file)), args.host, args.port) as server:
            server.serve_forever()
    finally:
        if background is not None:
            background.stop()
            background.join(timeout=1)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        raise SystemExit("calendar lab startup refused; inspect local config and permissions") from None

#!/usr/bin/env python3
"""Query a loopback lab API, printing counts/status only, never diary contents."""
import argparse
from datetime import datetime
import ipaddress
import json
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def summarize(payload):
    events = payload["events"]
    status = payload.get("calendar_status", {})
    return {"event_count": len(events), "calendar_count": len({event["calendar_id"] for event in events}),
            "stale": bool(status.get("stale", False)), "age_seconds": status.get("age_seconds")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:19080")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args(argv)
    url = urlsplit(args.base_url)
    if (url.scheme != "http" or not url.hostname or not ipaddress.ip_address(url.hostname).is_loopback
            or url.username or url.password or url.query or url.fragment or url.path not in ("", "/")):
        raise ValueError("loopback lab URL required")
    for value in (args.start, args.end):
        if datetime.fromisoformat(value).tzinfo is None:
            raise ValueError("timezone required")
    request = args.base_url.rstrip("/") + "/api/calendar?" + urlencode({"start": args.start, "end": args.end})
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=40) as response:
            payload = json.loads(response.read(4 * 1024 * 1024 + 1))
        print(json.dumps(summarize(payload)))
    except HTTPError as error:
        print(json.dumps({"status_code": error.code, "result": "unavailable"}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("lab check failed; no response body was logged") from None

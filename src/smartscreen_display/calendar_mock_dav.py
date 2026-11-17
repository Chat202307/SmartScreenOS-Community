"""Synthetic HTTPS CalDAV endpoint for isolated tests, never an Apple client."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import ssl
from threading import Lock
import time
from xml.sax.saxutils import escape


def event(lines):
    return "BEGIN:VEVENT\r\nDTSTAMP:20261001T000000Z\r\n" + lines.replace("\n", "\r\n") + "\r\nEND:VEVENT\r\n"


def calendar(*items):
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n" + "".join(items) + "END:VCALENDAR\r\n"


DATA = {
    "one": calendar(
        event("UID:recurring\nDTSTART;TZID=Asia/Shanghai:20261101T090000\nDTEND;TZID=Asia/Shanghai:20261101T100000\nRRULE:FREQ=DAILY;COUNT=4\nEXDATE;TZID=Asia/Shanghai:20261102T090000\nSUMMARY:Synthetic recurrence"),
        event("UID:recurring\nRECURRENCE-ID;TZID=Asia/Shanghai:20261103T090000\nDTSTART;TZID=Asia/Shanghai:20261103T140000\nDTEND;TZID=Asia/Shanghai:20261103T150000\nSUMMARY:Synthetic moved"),
        event("UID:recurring\nRECURRENCE-ID;TZID=Asia/Shanghai:20261104T090000\nSTATUS:CANCELLED"),
        event("UID:all-day\nDTSTART;VALUE=DATE:20261103\nDTEND;VALUE=DATE:20261105\nSUMMARY:Synthetic all day"),
        event("UID:dst\nDTSTART;TZID=America/New_York:20261031T090000\nDTEND;TZID=America/New_York:20261031T100000\nRRULE:FREQ=DAILY;COUNT=3\nSUMMARY:Synthetic DST"),
        event("UID:utc\nDTSTART:20261102T120000Z\nDTEND:20261102T130000Z\nSUMMARY:Synthetic UTC"),
        event("UID:floating\nDTSTART:20261103T173000\nDTEND:20261103T180000\nSUMMARY:Synthetic floating"),
    ),
    "two": calendar(event("UID:recurring\nDTSTART:20261101T010000Z\nDTEND:20261101T020000Z\nSUMMARY:Synthetic separate calendar")),
}


def dav_response(href, properties):
    return f"<d:response><d:href>{href}</d:href><d:propstat><d:prop>{properties}</d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>"


class MockDAV(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address):
        super().__init__(address, Handler)
        self.state = {"propfind": 0, "report": 0, "calendar_writes": 0, "mode": "normal"}
        self.lock = Lock()
    def handle_error(self, *args):
        pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def send(self, code, body, content_type="application/json"):
        raw = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except OSError:
            pass
    def do_GET(self):
        if self.path == "/_lab/stats":
            with self.server.lock:
                self.send(200, json.dumps(self.server.state))
        else:
            self.send(404, "{}")
    def do_POST(self):
        if self.path != "/_lab/scenario":
            return self.reject_write()
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 128:
                raise ValueError()
            mode = json.loads(self.rfile.read(size))["mode"]
            if mode not in ("normal", "timeout", "malformed", "slow"):
                raise ValueError()
            with self.server.lock:
                self.server.state["mode"] = mode
            self.send(200, "{}")
        except (ValueError, KeyError):
            self.send(400, "{}")
    def reject_write(self):
        with self.server.lock:
            self.server.state["calendar_writes"] += 1
        self.send(405, "{}")
    do_PUT = reject_write
    do_DELETE = reject_write
    do_PATCH = reject_write
    def dav(self):
        expected = "Basic " + base64.b64encode(b"fixture-user:fixture-password").decode()
        if self.headers.get("Authorization") != expected:
            return self.send(401, "{}")
        size = int(self.headers.get("Content-Length", "0"))
        if size > 65536:
            return self.send(413, "{}")
        self.rfile.read(size)
        kind = "propfind" if self.command == "PROPFIND" else "report"
        with self.server.lock:
            self.server.state[kind] += 1
            mode = self.server.state["mode"]
        if self.command == "REPORT":
            if mode == "timeout":
                time.sleep(3)
            elif mode == "slow":
                time.sleep(0.5)
            key = self.path.rstrip("/").rsplit("/", 1)[-1]
            data = "invalid synthetic ICS" if mode == "malformed" and key == "two" else DATA.get(key, "")
            body = dav_response(self.path + "synthetic.ics", "<c:calendar-data>" + escape(data) + "</c:calendar-data>")
            if key == "two" and mode == "missing-data":
                body = dav_response(self.path + "synthetic.ics", "<d:getetag>synthetic</d:getetag>")
            if key == "two" and mode == "denied-resource":
                body = body.replace("200 OK", "403 Forbidden")
        elif self.path == "/":
            body = dav_response("/", "<d:current-user-principal><d:href>/principal/</d:href></d:current-user-principal>")
        elif self.path == "/principal/":
            body = dav_response("/principal/", "<c:calendar-home-set><d:href>/home/</d:href></c:calendar-home-set>")
        else:
            props = '<d:resourcetype><d:collection/><c:calendar/></d:resourcetype><c:supported-calendar-component-set><c:comp name="VEVENT"/></c:supported-calendar-component-set>'
            body = "".join(dav_response("/home/" + key + "/", props) for key in DATA)
        self.send(207, '<d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">' + body + '</d:multistatus>', "application/xml")
    do_PROPFIND = dav
    do_REPORT = dav


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cert", required=True)
    parser.add_argument("--key", required=True)
    args = parser.parse_args(argv)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(args.cert, args.key)
    with MockDAV(("0.0.0.0", 8443)) as server:
        server.socket = context.wrap_socket(server.socket, server_side=True)
        server.serve_forever()


if __name__ == "__main__":
    main()

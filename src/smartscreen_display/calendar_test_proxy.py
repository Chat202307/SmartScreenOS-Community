"""Lab-only CONNECT proxy: verified global CalDAV endpoints (global and China) on port 443 only."""
import argparse
import ipaddress
import re
import select
import socket
import socketserver
import time


def destination(authority):
    match = re.fullmatch(r"((?:p[0-9]+-)?caldav\.icloud\.com(?:\.cn)?):443", authority.lower())
    if not match:
        raise ValueError("destination denied")
    return match.group(1), 443


def public_addresses(host, port):
    answers = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    addresses = list(dict.fromkeys(answer[4][0] for answer in answers))
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("destination denied")
    return addresses


def connect_destination(authority):
    host, port = destination(authority)
    # Connect to an already-checked IP; never resolve again during connect.
    for address in public_addresses(host, port):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.settimeout(10)
            connection.connect((address, port))
            return connection
        except OSError:
            connection.close()
    raise OSError("upstream unavailable")


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(10)
        upstream = None
        try:
            line = self.rfile.readline(4097)
            if len(line) > 4096:
                raise ValueError("request denied")
            method, authority, version = line.decode("ascii").strip().split()
            if method != "CONNECT" or version not in ("HTTP/1.0", "HTTP/1.1"):
                raise ValueError("request denied")
            # Drain bounded headers; do not inspect or log proxy credentials.
            size = len(line)
            while True:
                header = self.rfile.readline(4097)
                size += len(header)
                if not header or size > 16384:
                    raise ValueError("request denied")
                if header in (b"\r\n", b"\n"):
                    break
            upstream = connect_destination(authority)
            self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.wfile.flush()
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                ready, _, _ = select.select([self.connection, upstream], [], [], 1)
                for source in ready:
                    data = source.recv(65536)
                    if not data:
                        return
                    (upstream if source is self.connection else self.connection).sendall(data)
        except Exception:
            if upstream is None:
                try:
                    self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
                except OSError:
                    pass
        finally:
            if upstream is not None:
                upstream.close()


class Proxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    def handle_error(self, *args):
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3128)
    args = parser.parse_args(argv)
    with Proxy((args.host, args.port), Handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run tests with process-wide socket auditing: loopback fixtures only, no LAN/WAN.

The guard includes background threads. It is a test safeguard, not an OS sandbox;
subprocesses are not covered. Synthetic Docker scenarios use an internal network.
"""
import ipaddress
from pathlib import Path
import runpy
import socket
import sys
from urllib.parse import urlsplit
import urllib.request
from urllib.error import URLError


def permitted(host, port=None):
    if host == 'localhost':
        loopback = True
    else:
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = False
    return loopback and port not in (8123, 1883, 8883)


def audit(event, args):
    if event == 'socket.getaddrinfo' and not permitted(args[0], args[1]):
        raise OSError('offline test guard blocked non-fixture DNS/network access')
    if event in ('socket.connect', 'socket.sendto'):
        address = args[1] if event == 'socket.connect' else args[-1]
        if not isinstance(address, tuple) or not permitted(address[0], address[1]):
            raise OSError('offline test guard blocked non-fixture network access')


def guarded_urlopen(original):
    def open_fixture(request, *args, **kwargs):
        url = request.full_url if hasattr(request, 'full_url') else request
        target = urlsplit(url)
        if not permitted(target.hostname, target.port):
            raise URLError('offline test guard refused HTTP transport before network access')
        return original(request, *args, **kwargs)
    return open_fixture


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    # Install before importing application modules: their default opener arguments
    # must bind this refusing wrapper, never the real household HTTP transport.
    urllib.request.urlopen = guarded_urlopen(urllib.request.urlopen)
    sys.addaudithook(audit)
    args = sys.argv[1:]
    if args and args[0] == '--unittest':
        sys.argv = ['unittest', 'discover', '-s', 'tests', '-t', '.', '-v']
        runpy.run_module('unittest', run_name='__main__')
    elif args and args[0] == '--project-runner':
        sys.argv = ['tools/test_runner.py']
        runpy.run_path('tools/test_runner.py', run_name='__main__')
    else:
        import pytest
        raise SystemExit(pytest.main(args or ['tests', '-q']))


if __name__ == '__main__':
    main()

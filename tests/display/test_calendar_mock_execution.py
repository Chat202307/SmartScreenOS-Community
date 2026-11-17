from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
from threading import Thread
from unittest.mock import Mock

import pytest

from src.smartscreen_display.calendar_mock_dav import MockDAV
from src.smartscreen_display.calendar_test_server import mock_service
from src.smartscreen_display.calendar_config import CalendarConfig
from src.smartscreen_display.calendar_source import CalendarSourceError
from src.smartscreen_display.caldav_calendar_source import CalDAVCalendarSource
from tools.run_isolated_caldav_e2e import require_hosted_runner, main as runner_main


def test_real_loopback_tls_caldav_cache_expiry_and_partial_failure(tmp_path, monkeypatch):
    import caldav
    openssl = shutil.which("openssl")
    if openssl is None:
        pytest.skip("OpenSSL is needed for the ephemeral synthetic TLS certificate")
    cert, key, password = (tmp_path / name for name in ("cert.pem", "key.pem", "password"))
    subprocess.run([openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                    "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
                    "-keyout", str(key), "-out", str(cert)], check=True, capture_output=True)
    password.write_text("fixture-password")
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "*")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server = MockDAV(("127.0.0.1", 0))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        clock = [1000.0]
        config = CalendarConfig(enabled=True, provider="caldav", url=f"https://localhost:{server.server_port}/",
                                timeout_seconds=5, refresh_timeout_seconds=20)
        credentials = {config.username_env: "fixture-user", config.password_file_env: str(password)}
        source = CalDAVCalendarSource(config=config, clock=lambda: clock[0], environ=credentials,
            client_factory=lambda **options: caldav.DAVClient(**dict(options, ssl_verify_cert=str(cert))))
        start, end = datetime.fromisoformat("2026-10-30T00:00:00+08:00"), datetime.fromisoformat("2026-11-10T00:00:00+08:00")
        events = source.list_events(start, end)
        assert len(events) == 9 and server.state["report"] == 2
        clock[0] += 299
        assert source.list_events(start, end) == events and server.state["report"] == 2
        clock[0] += 1
        assert source.list_events(start, end) == events and server.state["report"] == 4
        for mode in ("malformed", "missing-data", "denied-resource"):
            server.state["mode"] = mode
            clock[0] += 300
            with pytest.raises(CalendarSourceError):
                source.list_events(start, end)
            assert next(iter(source._cache.values())).events == events
        server.state["mode"] = "normal"
        clock[0] += 30
        assert source.list_events(start, end) == events
        assert server.state["calendar_writes"] == 0
        # Same endpoint with the normal public CA set must reject the generated
        # self-signed fixture; the successful path did not disable TLS validation.
        untrusted = CalDAVCalendarSource(config=config, environ=credentials)
        with pytest.raises(CalendarSourceError):
            untrusted.list_events(start, end)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


@pytest.mark.parametrize("environment", [
    {}, {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "self-hosted", "RUNNER_OS": "Linux"},
    {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted", "RUNNER_OS": "Windows"},
    {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted", "RUNNER_OS": "Linux", "DOCKER_HOST": "tcp://nas:2375"},
    {"GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted", "RUNNER_OS": "Linux", "DOCKER_CONTEXT": "nas"},
])
def test_synthetic_docker_runner_refuses_work_self_hosted_and_remote_daemons(environment):
    with pytest.raises(RuntimeError):
        require_hosted_runner(environment)


def test_runner_dry_run_never_executes_docker_or_ssh(monkeypatch, capsys):
    command = Mock(side_effect=AssertionError("no Docker execution in dry-run"))
    monkeypatch.setattr("tools.run_isolated_caldav_e2e.command", command)
    runner_main([])
    command.assert_not_called()
    assert "No Docker or SSH" in capsys.readouterr().out


def test_mock_mode_rejects_non_synthetic_password_and_missing_ca(tmp_path):
    password, ca = tmp_path / "password", tmp_path / "ca.pem"
    password.write_text("not-a-synthetic-password")
    ca.write_text("synthetic-placeholder")
    with pytest.raises(ValueError):
        mock_service(ca, password, {"NO_PROXY": "*"})
    with pytest.raises(ValueError):
        mock_service(None, None, {"NO_PROXY": "*"})


def test_offline_runner_blocks_household_and_internet_before_socket_access():
    from tools.run_offline_tests import audit
    for address in (("192.0.2.2", 8123), ("demo-nas.local", 22),
                    ("caldav.icloud.com", 443), ("127.0.0.1", 1883)):
        with pytest.raises(OSError, match="offline test guard"):
            audit("socket.connect", (None, address))
        with pytest.raises(OSError, match="offline test guard"):
            audit("socket.getaddrinfo", address)
    audit("socket.connect", (None, ("127.0.0.1", 45678)))


def test_offline_http_guard_refuses_before_calling_real_transport():
    from tools.run_offline_tests import guarded_urlopen
    from urllib.error import URLError
    original = Mock(side_effect=AssertionError("real HTTP transport must not run"))
    with pytest.raises(URLError, match="before network access"):
        guarded_urlopen(original)("http://192.0.2.2:8123/api/states")
    original.assert_not_called()

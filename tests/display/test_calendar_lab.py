import json
from pathlib import Path
import socket
from threading import Thread
from unittest.mock import Mock

import pytest
import yaml

from src.smartscreen_display.calendar_test_server import (
    CalendarProbe, create_probe_server, fixture_service, isolated_environment, live_service, PROXY,
)
from src.smartscreen_display import calendar_test_proxy as proxy
from tools.check_calendar_lab import summarize
from tools.check_lab_permissions import check

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "deploy/caldav-lab"


@pytest.mark.parametrize("method,path", [
    ("POST", "/api/calendar"), ("POST", "/api/device/control"),
    ("PUT", "/api/todos"), ("DELETE", "/api/todos"), ("PATCH", "/api/home"),
    ("GET", "/api/todos"), ("GET", "/api/devices"), ("GET", "/"),
])
def test_probe_never_delegates_household_routes(method, path):
    probe = CalendarProbe(Mock())
    probe._calendar = Mock()
    assert probe.handle(method, path)[0] in (404, 405)
    probe._calendar.handle.assert_not_called()


def test_probe_serves_fixture_over_real_http_without_household_runtime():
    from http.client import HTTPConnection
    probe = CalendarProbe(fixture_service(LAB / "fixtures/events.json"))
    server = create_probe_server(probe, port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(*server.server_address, timeout=10)
        conn.request("GET", "/api/calendar?start=2026-11-14T00:00:00%2B08:00&end=2026-11-15T00:00:00%2B08:00")
        response = conn.getresponse()
        assert response.status == 200
        payload = json.loads(response.read())
        assert summarize(payload) == {"event_count": 2, "calendar_count": 2, "stale": False, "age_seconds": None}
        conn.close()
        conn = HTTPConnection(*server.server_address, timeout=10)
        conn.request("POST", "/api/device/control", body=b"test")
        response = conn.getresponse()
        assert response.status == 405
        response.read()
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


@pytest.mark.parametrize("env", [
    {"SMARTSCREEN_HA_TOKEN": "test-secret"}, {"SMARTSCREEN_DNAKE_MQTT_HOST": "broker"},
    {"SMARTSCREEN_XINGOO_PASSWORD": "test-secret"}, {"HTTPS_PROXY": "http://wrong:3128"},
    {"HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY, "NO_PROXY": "icloud.com"},
    {"HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY, "https_proxy": "http://wrong:3128"},
])
def test_live_probe_rejects_household_env_and_proxy_bypass(env):
    with pytest.raises(ValueError) as error:
        isolated_environment(env, live=True)
    assert "test-secret" not in str(error.value)


def test_live_credentials_stay_in_private_source_mapping(tmp_path, monkeypatch):
    from src.smartscreen_display import caldav_calendar_source as module
    username, password = tmp_path / "username", tmp_path / "password"
    username.write_text("synthetic@example.invalid")
    password.write_text("test-only-secret")
    factory = Mock()
    monkeypatch.setattr(module, "CalDAVCalendarSource", factory)
    environ = {"HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY, "NO_PROXY": "", "ALL_PROXY": ""}
    live_service(LAB / "fixtures/calendar.json", username, password, environ)
    assert set(environ) == {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY"}
    credentials = factory.call_args.kwargs["environ"]
    assert credentials["SMARTSCREEN_ICLOUD_USERNAME"] == "synthetic@example.invalid"
    assert credentials["SMARTSCREEN_ICLOUD_PASSWORD_FILE"] == str(password)
    factory.return_value.list_events.assert_not_called()  # no network on startup


def test_live_probe_rejects_non_icloud_config_before_reading_secrets(tmp_path, monkeypatch):
    config = tmp_path / "calendar.json"
    config.write_text(json.dumps({"enabled": True, "provider": "caldav", "url": "https://homeassistant:8123/"}))
    reader = Mock()
    monkeypatch.setattr("src.smartscreen_display.calendar_test_server.secret_text", reader)
    with pytest.raises(ValueError):
        live_service(config, tmp_path / "missing-user", tmp_path / "missing-password",
                     {"HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY})
    reader.assert_not_called()


@pytest.mark.parametrize("authority", [
    "mosquitto:1883", "homeassistant:8123", "192.0.2.3:443", "127.0.0.1:443",
    "caldav.icloud.com.evil.invalid:443", "caldav.icloud.com:80", "demo_5@example.invalid:443",
    "caldav.icloud.com:443/path", "[::1]:443", "example.invalid:443",
    "p123-caldav.icloud.com.cn.evil.invalid:443", "other.icloud.com.cn:443",
    "evil-caldav.icloud.com.cn:443", "caldav.icloud.com.cn:80",
])
def test_proxy_denies_non_caldav_destinations_before_dns(authority, monkeypatch):
    resolver = Mock()
    monkeypatch.setattr(socket, "getaddrinfo", resolver)
    with pytest.raises(ValueError):
        proxy.connect_destination(authority)
    resolver.assert_not_called()


@pytest.mark.parametrize("address", ["127.0.0.1", "192.0.2.1", "172.29.4.3", "192.0.2.3", "169.254.169.254", "0.0.0.0"])
def test_proxy_blocks_rebinding_to_private_or_non_global_addresses(address, monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))])
    connector = Mock()
    monkeypatch.setattr(socket, "socket", connector)
    with pytest.raises(ValueError):
        proxy.connect_destination("caldav.icloud.com:443")
    connector.assert_not_called()


def test_proxy_connects_checked_ip_not_hostname(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("17.253.144.10", 443))])
    stream = Mock()
    monkeypatch.setattr(socket, "socket", lambda *args: stream)
    assert proxy.connect_destination("p123-caldav.icloud.com:443") is stream
    stream.connect.assert_called_once_with(("17.253.144.10", 443))


def test_proxy_protocol_refuses_plain_http_without_upstream(monkeypatch):
    from http.client import HTTPConnection
    connector = Mock()
    monkeypatch.setattr(proxy, "connect_destination", connector)
    with proxy.Proxy(("127.0.0.1", 0), proxy.Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            conn = HTTPConnection(*server.server_address, timeout=10)
            conn.request("GET", "http://homeassistant:8123/")
            response = conn.getresponse()
            assert response.status == 403
            response.read()
            conn.close()
        finally:
            server.shutdown()
            thread.join(timeout=10)
    connector.assert_not_called()


def test_compose_isolation_contract():
    offline = yaml.safe_load((LAB / "compose.yaml").read_text())
    live = yaml.safe_load((LAB / "compose.live.yaml").read_text())
    assert offline["networks"]["calendar-lab"]["internal"] is True
    probe = offline["services"]["calendar-probe"]
    assert "ports" not in probe and probe["expose"] == ["19081"]
    assert probe["command"][probe["command"].index("--port") + 1] == "19081"
    live_command = live["services"]["calendar-probe"]["command"]
    assert live_command[live_command.index("--port") + 1] == "19081"
    assert probe["networks"] == ["calendar-lab"]
    assert "calendar_test_server" in probe["entrypoint"][-1]
    assert live["services"]["egress-proxy"]["networks"] == ["calendar-lab", "calendar-egress"]
    for service in [probe, live["services"]["egress-proxy"]]:
        assert service["user"] == "10001:10001"
        assert service["read_only"] is True and service["cap_drop"] == ["ALL"]
        assert "env_file" not in service and "privileged" not in service
        assert "host" not in service.get("networks", [])
        for mount in service.get("volumes", []):
            assert mount["target"] == "/lab" and mount["read_only"] is True
            assert mount["bind"]["create_host_path"] is False
    assert "ports" not in live["services"]["egress-proxy"]
    assert set(live["services"]["calendar-probe"]["environment"]) == {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY"}


@pytest.mark.parametrize("path", ["/persistent", "/share/test", "/test-data/../persistent"])
def test_permission_probe_refuses_production_and_arbitrary_paths(path):
    with pytest.raises(ValueError):
        check(path, write_probe=True)


def test_permission_probe_refuses_wrong_uid(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 0)
    with pytest.raises(ValueError):
        check("/test-data", write_probe=True)


def test_permission_probe_requires_test_tmpfs_and_never_changes_modes(monkeypatch):
    monkeypatch.setattr("os.geteuid", lambda: 10001)
    monkeypatch.setattr("os.getegid", lambda: 10001)
    monkeypatch.setattr("os.access", lambda *args: True)
    monkeypatch.setattr(Path, "read_text", lambda self: "1 0 0:1 / /test-data rw - ext4 /dev/test rw\n")
    with pytest.raises(ValueError):
        check("/test-data", write_probe=True)
    monkeypatch.setattr(Path, "read_text", lambda self: "1 0 0:1 / /test-data rw - tmpfs tmpfs rw\n")
    writer = Mock()
    monkeypatch.setattr("tempfile.TemporaryFile", writer)
    writer.return_value.__enter__ = Mock(return_value=Mock())
    writer.return_value.__exit__ = Mock(return_value=False)
    chmod = Mock(side_effect=AssertionError("never change modes"))
    monkeypatch.setattr("os.chmod", chmod)
    assert check("/test-data", write_probe=True)
    writer.assert_called_once_with(dir=Path("/test-data"))
    chmod.assert_not_called()


def test_summary_does_not_emit_private_diary_data():
    payload = {"events": [{"calendar_id": "PRIVATE_CALENDAR", "title": "PRIVATE_DIARY"}],
               "calendar_status": {"state": "fresh", "stale": False, "age_seconds": 2}}
    assert "PRIVATE" not in json.dumps(summarize(payload))


@pytest.mark.parametrize('host', ['caldav.icloud.com.cn', 'p123-caldav.icloud.com.cn'])
def test_china_proxy_uses_same_public_ip_pinning(host, monkeypatch):
    monkeypatch.setattr(socket, 'getaddrinfo', lambda *args: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('17.253.144.10', 443))])
    stream = Mock()
    monkeypatch.setattr(socket, 'socket', lambda *args: stream)
    assert proxy.connect_destination(host + ':443') is stream
    stream.connect.assert_called_once_with(('17.253.144.10', 443))

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import math
import re


@dataclass(frozen=True)
class CalendarConfig:
    enabled: bool
    provider: str | None = None
    calendar_id: str | None = None
    bridge_executable: str | None = None
    url: str = "https://caldav.icloud.com/"
    timezone: str = "Asia/Shanghai"
    timeout_seconds: float = 30
    refresh_timeout_seconds: float = 120
    allow_stale: bool = False
    username_file_env: str | None = None
    username_env: str = "SMARTSCREEN_ICLOUD_USERNAME"
    password_file_env: str = "SMARTSCREEN_ICLOUD_PASSWORD_FILE"


def load_calendar_config(
    path: Path,
) -> CalendarConfig:
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "calendar config must be an object"
        )

    enabled = payload.get("enabled", False)

    if not isinstance(enabled, bool):
        raise ValueError(
            "calendar enabled must be boolean"
        )

    if not enabled:
        return CalendarConfig(enabled=False)

    provider = payload.get("provider")
    calendar_id = payload.get("calendar_id")
    bridge_executable = payload.get(
        "bridge_executable"
    )

    if provider not in ("eventkit", "caldav"):
        raise ValueError(
            "unsupported calendar provider"
        )

    if calendar_id is not None:
        if (
            not isinstance(calendar_id, str)
            or not calendar_id.strip()
        ):
            raise ValueError(
                "calendar_id must be a non-blank string or null"
            )

        calendar_id = calendar_id.strip()

    if provider == "caldav":
        # Configuration stores secret references only, never credential values.
        allowed = {"schema_version", "enabled", "provider", "calendar_id", "url",
                   "timezone", "timeout_seconds", "refresh_timeout_seconds", "allow_stale",
                   "username_env", "username_file_env", "password_file_env"}
        if payload.keys() - allowed:
            raise ValueError("unsupported CalDAV setting; use runtime secret references for credentials")
        url = payload.get("url", "https://caldav.icloud.com/")
        if not isinstance(url, str):
            raise ValueError("CalDAV url must be HTTPS without credentials")
        try:
            parts = urlsplit(url)
            valid_url = (parts.scheme == "https" and parts.hostname
                         and not parts.username and not parts.password
                         and not parts.query and not parts.fragment)
            parts.port
        except ValueError:
            valid_url = False
        if not valid_url:
            raise ValueError("CalDAV url must be HTTPS without credentials")
        timezone = payload.get("timezone", "Asia/Shanghai")
        try:
            ZoneInfo(timezone)
        except (TypeError, ValueError, ZoneInfoNotFoundError):
            raise ValueError("invalid calendar timezone") from None
        timeout = payload.get("timeout_seconds", 30)
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or not 0 < timeout <= 60):
            raise ValueError("timeout_seconds must be between 0 and 60")
        refresh_timeout = payload.get("refresh_timeout_seconds", 120)
        if (isinstance(refresh_timeout, bool) or not isinstance(refresh_timeout, (int, float))
                or not math.isfinite(refresh_timeout) or not 0 < refresh_timeout <= 120):
            raise ValueError("refresh_timeout_seconds must be between 0 and 120")
        allow_stale = payload.get("allow_stale", False)
        if not isinstance(allow_stale, bool):
            raise ValueError("allow_stale must be boolean")
        references = {}
        for key, default in (
            ("username_env", "SMARTSCREEN_ICLOUD_USERNAME"),
            ("password_file_env", "SMARTSCREEN_ICLOUD_PASSWORD_FILE"),
        ):
            value = payload.get(key, default)
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
                raise ValueError("invalid calendar secret reference")
            references[key] = value
        username_file_env = payload.get('username_file_env')
        if username_file_env is not None and (not isinstance(username_file_env, str)
                or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', username_file_env)):
            raise ValueError('invalid calendar secret reference')
        return CalendarConfig(
            username_file_env=username_file_env,
            enabled=True, provider=provider, calendar_id=calendar_id,
            url=url, timezone=timezone, timeout_seconds=timeout, **references,
            refresh_timeout_seconds=refresh_timeout, allow_stale=allow_stale,
        )

    if (
        not isinstance(bridge_executable, str)
        or not bridge_executable.strip()
    ):
        raise ValueError(
            "bridge_executable is required"
        )

    return CalendarConfig(
        enabled=True,
        provider=provider,
        calendar_id=calendar_id,
        bridge_executable=bridge_executable.strip(),
    )

from __future__ import annotations

from datetime import datetime
from typing import TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.smartscreen_runtime.runtime.capability_api import (
    Capability,
    CapabilityContext,
)


class ClockSnapshot(TypedDict):
    timezone: str
    timeFormat: str
    time: str
    date: str
    weekday: str
    iso: str


class ClockCapability(Capability):
    """Provide current date and time information for a configured timezone."""

    DEFAULT_TIMEZONE = "Asia/Shanghai"
    DEFAULT_TIME_FORMAT = "24h"
    SUPPORTED_TIME_FORMATS = frozenset({"12h", "24h"})

    def __init__(self) -> None:
        self.started = False
        self.context: CapabilityContext | None = None
        self._timezone_name = self.DEFAULT_TIMEZONE
        self._timezone = ZoneInfo(self.DEFAULT_TIMEZONE)
        self._time_format = self.DEFAULT_TIME_FORMAT

    def start(self, context: CapabilityContext) -> None:
        timezone_name = context.configuration.get(
            "timezone",
            self.DEFAULT_TIMEZONE,
        )
        time_format = context.configuration.get(
            "timeFormat",
            self.DEFAULT_TIME_FORMAT,
        )

        if not isinstance(timezone_name, str) or not timezone_name.strip():
            raise ValueError("Clock timezone must be a non-empty string.")

        if time_format not in self.SUPPORTED_TIME_FORMATS:
            raise ValueError(
                "Clock time format must be either '12h' or '24h'."
            )

        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"Invalid clock timezone: {timezone_name}"
            ) from exc

        self.context = context
        self._timezone_name = timezone_name
        self._timezone = timezone
        self._time_format = time_format
        self.started = True

    def stop(self) -> None:
        self.started = False

    def snapshot(self) -> ClockSnapshot:
        if not self.started:
            raise RuntimeError("Clock capability is not running.")

        now = datetime.now(self._timezone)

        if self._time_format == "12h":
            time_value = now.strftime("%I:%M:%S %p")
        else:
            time_value = now.strftime("%H:%M:%S")

        return {
            "timezone": self._timezone_name,
            "timeFormat": self._time_format,
            "time": time_value,
            "date": now.strftime("%Y-%m-%d"),
            "weekday": now.strftime("%A"),
            "iso": now.isoformat(),
        }

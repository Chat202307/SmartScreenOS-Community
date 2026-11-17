from datetime import datetime

import pytest

from src.smartscreen_runtime.runtime.engine import RuntimeEngine


def start_clock(configuration=None):
    engine = RuntimeEngine()
    capability = engine.install("examples/capabilities/clock")

    if configuration is not None:
        capability.manifest.configuration.clear()
        capability.manifest.configuration.update(configuration)

    session = engine.start(
        capability.capability_id,
        session_id="session-clock-001",
    )

    return engine, session, engine.get_instance(session.session_id)


def test_clock_returns_snapshot():
    engine, session, clock = start_clock(
        {
            "timezone": "Asia/Shanghai",
            "timeFormat": "24h",
        }
    )

    snapshot = clock.snapshot()

    assert snapshot["timezone"] == "Asia/Shanghai"
    assert snapshot["timeFormat"] == "24h"
    assert isinstance(snapshot["time"], str)
    assert isinstance(snapshot["date"], str)
    assert isinstance(snapshot["weekday"], str)
    assert isinstance(snapshot["iso"], str)

    parsed = datetime.fromisoformat(snapshot["iso"])
    assert parsed.tzinfo is not None

    engine.stop(session.session_id)


def test_clock_uses_24_hour_format():
    engine, session, clock = start_clock(
        {
            "timezone": "Asia/Shanghai",
            "timeFormat": "24h",
        }
    )

    value = clock.snapshot()["time"]

    assert len(value) == 8
    assert value.count(":") == 2

    engine.stop(session.session_id)


def test_clock_uses_12_hour_format():
    engine, session, clock = start_clock(
        {
            "timezone": "Asia/Shanghai",
            "timeFormat": "12h",
        }
    )

    value = clock.snapshot()["time"]

    assert value.endswith(("AM", "PM"))

    engine.stop(session.session_id)


def test_clock_rejects_invalid_timezone():
    with pytest.raises(Exception) as exc_info:
        start_clock(
            {
                "timezone": "Invalid/Timezone",
                "timeFormat": "24h",
            }
        )

    assert "timezone" in str(exc_info.value).lower()


def test_clock_rejects_invalid_time_format():
    with pytest.raises(Exception) as exc_info:
        start_clock(
            {
                "timezone": "Asia/Shanghai",
                "timeFormat": "invalid",
            }
        )

    assert "format" in str(exc_info.value).lower()


def test_clock_requires_running_state():
    engine, session, clock = start_clock(
        {
            "timezone": "Asia/Shanghai",
            "timeFormat": "24h",
        }
    )

    engine.stop(session.session_id)

    with pytest.raises(RuntimeError):
        clock.snapshot()

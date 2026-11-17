from datetime import datetime, timezone
from typing import get_type_hints

from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler
from src.smartscreen_runtime.runtime.snapshot_schema import HostSnapshot


FIXED_TIME = datetime(
    2026,
    8,
    7,
    14,
    10,
    0,
    tzinfo=timezone.utc,
)


def create_host():
    engine = RuntimeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=1,
        start_time=100.0,
    )

    return RuntimeHost(
        engine=engine,
        scheduler=scheduler,
        wall_clock=lambda: FIXED_TIME,
    )


def test_host_snapshot_schema_contains_generated_at():
    hints = get_type_hints(HostSnapshot)

    assert "generatedAt" in hints
    assert hints["generatedAt"] is str


def test_host_snapshot_contains_generated_at():
    host = create_host()

    snapshot = host.snapshot()

    assert (
        snapshot["generatedAt"]
        == "2026-08-07T14:10:00+00:00"
    )


def test_generated_at_is_top_level():
    host = create_host()

    snapshot = host.snapshot()

    assert "generatedAt" in snapshot
    assert "generatedAt" not in snapshot["runtime"]
    assert "generatedAt" not in snapshot["scheduler"]


def test_generated_at_changes_between_snapshots():
    times = iter(
        [
            datetime(
                2026,
                8,
                7,
                14,
                10,
                tzinfo=timezone.utc,
            ),
            datetime(
                2026,
                8,
                7,
                14,
                11,
                tzinfo=timezone.utc,
            ),
        ]
    )

    engine = RuntimeEngine()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=1,
        start_time=100.0,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
        wall_clock=lambda: next(times),
    )

    first = host.snapshot()
    second = host.snapshot()

    assert first["generatedAt"] != second["generatedAt"]

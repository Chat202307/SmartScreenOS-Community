from typing import get_type_hints

from src.smartscreen_runtime.runtime.engine import RuntimeEngine
from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler
from src.smartscreen_runtime.runtime.snapshot_schema import (
    HostSnapshot,
    SNAPSHOT_SCHEMA_VERSION,
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
    )


def test_snapshot_schema_version_constant():
    assert SNAPSHOT_SCHEMA_VERSION == "1.0"


def test_host_snapshot_schema_contains_version():
    hints = get_type_hints(HostSnapshot)

    assert "schemaVersion" in hints
    assert hints["schemaVersion"] is str


def test_host_snapshot_reports_schema_version():
    host = create_host()

    snapshot = host.snapshot()

    assert snapshot["schemaVersion"] == "1.0"


def test_schema_version_is_top_level():
    host = create_host()

    snapshot = host.snapshot()

    assert "schemaVersion" in snapshot
    assert "schemaVersion" not in snapshot["runtime"]
    assert "schemaVersion" not in snapshot["scheduler"]

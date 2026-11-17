from src.smartscreen_runtime.runtime.host import RuntimeHost
from src.smartscreen_runtime.runtime.scheduler import RuntimeScheduler


class SnapshotInstance:
    def snapshot(self):
        return {"value": 42}


class PublicEngineOnly:
    def __init__(self):
        self.instance = SnapshotInstance()

    def tick(self):
        return {}

    def snapshot(self):
        return {
            "installed": [],
            "sessions": [],
        }

    def list_instances(self):
        return (
            ("session-public-001", self.instance),
        )


def test_host_uses_public_instance_listing_api():
    engine = PublicEngineOnly()

    scheduler = RuntimeScheduler(
        engine,
        interval_seconds=10,
        start_time=100.0,
    )

    host = RuntimeHost(
        engine=engine,
        scheduler=scheduler,
    )

    snapshot = host.snapshot()

    assert snapshot["capabilities"] == {
        "session-public-001": {
            "value": 42,
        }
    }

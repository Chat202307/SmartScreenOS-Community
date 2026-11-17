from __future__ import annotations

from .observation_bridge import (
    DeviceObservationBridge,
)
from .registry import (
    DeviceRegistry,
)
from .store import (
    DeviceParameterStore,
)


class DeviceDataIngestionService:
    def __init__(
        self,
        *,
        registry: DeviceRegistry,
        store: DeviceParameterStore,
    ):
        self._registry = registry
        self._store = store
        self._bridge = DeviceObservationBridge(
            registry=registry
        )

    def ingest(
        self,
        *,
        adapter_id,
        source_id,
        value,
        available=True,
    ):
        entry = self._store.update_source(
            adapter_id=adapter_id,
            source_id=source_id,
            value=value,
            available=available,
        )

        return self._bridge.convert(
            entry,
            source_id=source_id,
        )

    def restore(
        self,
        *,
        adapter_id,
        source_id,
        value,
        available=True,
    ):
        return self._store.restore_source(
            adapter_id=adapter_id,
            source_id=source_id,
            value=value,
            available=available,
        )

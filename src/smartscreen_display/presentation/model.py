from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class DashboardCard:
    kind: str
    target: str
    value: Any
    confidence: float
    location_id: Optional[str] = None
    location_label: Optional[str] = None
    location_order: Optional[float] = None
    evidence_refs: Tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)
    updated_at: Optional[str] = None

    def to_dict(self):
        payload = {
            "kind": self.kind,
            "target": self.target,
            "value": self.value,
            "confidence": self.confidence,
            "location_id": self.location_id,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
        }

        if self.updated_at is not None:
            payload["updated_at"] = self.updated_at

        if self.location_label is not None:
            payload["location_label"] = (
                self.location_label
            )

        if self.location_order is not None:
            payload["location_order"] = (
                self.location_order
            )

        return payload


@dataclass(frozen=True)
class DashboardObservation:
    observation_id: str
    parameter: str
    value: Any
    unit: Optional[str]
    confidence: float
    quality: str
    location_id: Optional[str] = None
    location_label: Optional[str] = None
    location_order: Optional[float] = None
    observed_at: Optional[str] = None
    provenance: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        payload = {
            "observation_id": self.observation_id,
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence,
            "quality": self.quality,
            "location_id": self.location_id,
            "observed_at": self.observed_at,
            "provenance": dict(self.provenance),
            "metadata": dict(self.metadata),
        }

        if self.location_label is not None:
            payload["location_label"] = (
                self.location_label
            )

        if self.location_order is not None:
            payload["location_order"] = (
                self.location_order
            )

        return payload



@dataclass(frozen=True)
class DashboardLocation:
    location_id: str
    location_label: Optional[str] = None
    location_order: Optional[float] = None
    has_semantic_data: bool = False
    semantic_targets: Tuple[str, ...] = ()

    def to_dict(self):
        payload = {
            "location_id": self.location_id,
            "has_semantic_data": (
                self.has_semantic_data
            ),
            "semantic_targets": list(
                self.semantic_targets
            ),
        }

        if self.location_label is not None:
            payload["location_label"] = (
                self.location_label
            )

        if self.location_order is not None:
            payload["location_order"] = (
                self.location_order
            )

        return payload


@dataclass(frozen=True)
class DashboardZone:
    zone_id: str
    room_ids: Tuple[str, ...] = ()
    summary_location_id: Optional[str] = None
    location_label: Optional[str] = None
    location_order: Optional[float] = None
    show_on_home: bool = False
    sheet_extra_device_ids: Tuple[str, ...] = ()
    sheet_device_order: Tuple[str, ...] = ()
    sheet_wide_device_ids: Tuple[str, ...] = ()

    def to_dict(self):
        payload = {
            "zone_id": self.zone_id,
            "room_ids": list(self.room_ids),
        }

        if self.summary_location_id is not None:
            payload["summary_location_id"] = (
                self.summary_location_id
            )

        if self.location_label is not None:
            payload["location_label"] = (
                self.location_label
            )

        if self.location_order is not None:
            payload["location_order"] = (
                self.location_order
            )

        if self.show_on_home:
            payload["show_on_home"] = True

        if self.sheet_extra_device_ids:
            payload[
                "sheet_extra_device_ids"
            ] = list(
                self.sheet_extra_device_ids
            )

        if self.sheet_device_order:
            payload["sheet_device_order"] = list(
                self.sheet_device_order
            )

        if self.sheet_wide_device_ids:
            payload[
                "sheet_wide_device_ids"
            ] = list(
                self.sheet_wide_device_ids
            )

        return payload


@dataclass(frozen=True)
class DashboardViewModel:
    cards: Tuple[DashboardCard, ...] = ()
    observations: Tuple[DashboardObservation, ...] = ()
    locations: Tuple[DashboardLocation, ...] = ()
    zones: Tuple[DashboardZone, ...] = ()

    def to_dict(self):
        payload = {
            "cards": [
                card.to_dict()
                for card in self.cards
            ],
            "observations": [
                observation.to_dict()
                for observation in self.observations
            ],
            "locations": [
                location.to_dict()
                for location in self.locations
            ],
        }

        if self.zones:
            payload["zones"] = [
                zone.to_dict()
                for zone in self.zones
            ]

        return payload

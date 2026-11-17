from __future__ import annotations

from .model import (
    DashboardCard,
    DashboardLocation,
    DashboardObservation,
    DashboardViewModel,
    DashboardZone,
)


class DashboardPresentationBuilder:
    def __init__(
        self,
        *,
        location_labels=None,
        location_orders=None,
        location_zones=None,
    ):
        self._location_labels = dict(
            location_labels or {}
        )
        self._location_orders = dict(
            location_orders or {}
        )
        self._location_zones = dict(
            location_zones or {}
        )

    def build(
        self,
        *,
        household_states,
        observations=(),
    ):
        cards = tuple(
            DashboardCard(
                kind="state",
                target=item["target"],
                value=item["value"],
                confidence=float(item["confidence"]),
                location_id=item.get("location_id"),
                location_label=self._location_label(
                    item.get("location_id")
                ),
                location_order=self._location_order(
                    item.get("location_id")
                ),
                evidence_refs=tuple(
                    item.get("evidence_refs", ())
                ),
                metadata=dict(
                    item.get("metadata", {})
                ),
                updated_at=item.get(
                    "updated_at"
                ),
            )
            for item in household_states
        )

        dashboard_observations = tuple(
            DashboardObservation(
                observation_id=(
                    item.observation_id
                ),
                parameter=item.parameter,
                value=item.value,
                unit=item.unit,
                confidence=float(
                    item.confidence
                ),
                quality=item.quality,
                location_id=item.location_id,
                location_label=(
                    self._location_label(
                        item.location_id
                    )
                ),
                location_order=(
                    self._location_order(
                        item.location_id
                    )
                ),
                observed_at=item.observed_at,
                provenance=dict(
                    item.provenance or {}
                ),
                metadata=dict(
                    item.metadata or {}
                ),
            )
            for item in observations
        )

        locations = self._build_locations(
            household_states,
            observations=observations,
        )

        zones = tuple(
            DashboardZone(
                zone_id=zone_id,
                room_ids=self._zone_room_ids(
                    zone_config
                ),
                summary_location_id=(
                    self._zone_summary_location_id(
                        zone_config
                    )
                ),
                show_on_home=(
                    self._zone_show_on_home(
                        zone_config
                    )
                ),
                sheet_extra_device_ids=(
                    self._zone_string_tuple(
                        zone_config,
                        "sheet_extra_device_ids",
                    )
                ),
                sheet_device_order=(
                    self._zone_string_tuple(
                        zone_config,
                        "sheet_device_order",
                    )
                ),
                sheet_wide_device_ids=(
                    self._zone_string_tuple(
                        zone_config,
                        "sheet_wide_device_ids",
                    )
                ),
                location_label=(
                    self._location_label(
                        zone_id
                    )
                ),
                location_order=(
                    self._location_order(
                        zone_id
                    )
                ),
            )
            for zone_id, zone_config
            in sorted(
                self._location_zones.items(),
                key=lambda item: (
                    self._location_order(
                        item[0]
                    ) is None,
                    (
                        self._location_order(
                            item[0]
                        )
                        if self._location_order(
                            item[0]
                        ) is not None
                        else 0
                    ),
                    item[0],
                ),
            )
        )

        return DashboardViewModel(
            cards=cards,
            observations=(
                dashboard_observations
            ),
            locations=locations,
            zones=zones,
        )

    @staticmethod
    def _zone_room_ids(zone_config):
        if isinstance(zone_config, dict):
            room_ids = zone_config.get(
                "room_ids",
                (),
            )
        else:
            room_ids = zone_config

        return tuple(
            room_ids or ()
        )


    @staticmethod
    def _zone_summary_location_id(
        zone_config
    ):
        if not isinstance(
            zone_config,
            dict,
        ):
            return None

        value = zone_config.get(
            "summary_location_id"
        )

        if value is None:
            return None

        return str(value)


    @staticmethod
    def _zone_string_tuple(
        zone_config,
        key,
    ):
        if not isinstance(
            zone_config,
            dict,
        ):
            return ()

        value = zone_config.get(
            key,
            (),
        )

        if not isinstance(
            value,
            (list, tuple),
        ):
            return ()

        return tuple(
            item
            for item in value
            if (
                isinstance(item, str)
                and item
            )
        )


    @staticmethod
    def _zone_show_on_home(zone_config):
        if not isinstance(
            zone_config,
            dict,
        ):
            return False

        return (
            zone_config.get(
                "show_on_home"
            ) is True
        )


    def _location_label(self, location_id):
        if location_id is None:
            return None

        return self._location_labels.get(
            location_id
        )


    def _location_order(self, location_id):
        if location_id is None:
            return None

        return self._location_orders.get(
            location_id
        )


    def _build_locations(
        self,
        household_states,
        *,
        observations=(),
    ):
        room_semantic_targets = {
            "occupancy",
            "comfort",
            "lighting",
        }

        semantic_targets_by_location = {}
        state_locations = set()

        for item in household_states:
            location_id = item.get(
                "location_id"
            )

            if location_id is None:
                continue

            state_locations.add(
                location_id
            )

            target = item["target"]

            if target not in room_semantic_targets:
                continue

            semantic_targets_by_location.setdefault(
                location_id,
                set(),
            ).add(
                target
            )

        semantic_locations = set(
            semantic_targets_by_location
        )

        observation_locations = {
            item.location_id
            for item in observations
            if item.location_id is not None
        }

        known_locations = (
            set(self._location_labels)
            | set(self._location_orders)
            | state_locations
            | observation_locations
        )

        locations = [
            DashboardLocation(
                location_id=location_id,
                location_label=(
                    self._location_label(
                        location_id
                    )
                ),
                location_order=(
                    self._location_order(
                        location_id
                    )
                ),
                has_semantic_data=(
                    location_id
                    in semantic_locations
                ),
                semantic_targets=tuple(
                    sorted(
                        semantic_targets_by_location.get(
                            location_id,
                            (),
                        ),
                        key=lambda target: (
                            0
                            if target == "occupancy"
                            else 1
                            if target == "comfort"
                            else 2
                            if target == "lighting"
                            else 100,
                            target,
                        ),
                    )
                ),
            )
            for location_id in known_locations
        ]

        locations.sort(
            key=lambda item: (
                item.location_order is None,
                (
                    item.location_order
                    if item.location_order is not None
                    else 0
                ),
                item.location_id,
            )
        )

        return tuple(locations)

from __future__ import annotations

from datetime import datetime, timezone


class ObservationAccumulator:
    """Keep the latest fresh observation for each parameter and location."""

    def __init__(
        self,
        *,
        max_age_seconds=None,
        max_age_by_parameter=None,
        max_age_by_location_parameter=None,
        clock=None,
    ):
        if (
            max_age_seconds is not None
            and (
                isinstance(max_age_seconds, bool)
                or not isinstance(
                    max_age_seconds,
                    (int, float),
                )
                or max_age_seconds <= 0
            )
        ):
            raise ValueError(
                "max_age_seconds must be greater than zero"
            )

        parameter_policy = dict(
            max_age_by_parameter or {}
        )

        for max_age in parameter_policy.values():
            if (
                isinstance(max_age, bool)
                or not isinstance(
                    max_age,
                    (int, float),
                )
            ):
                raise ValueError(
                    "parameter max age must be a positive number"
                )

            if max_age <= 0:
                raise ValueError(
                    "parameter max age must be greater than zero"
                )

        location_parameter_policy = dict(
            max_age_by_location_parameter or {}
        )

        for max_age in location_parameter_policy.values():
            if (
                isinstance(max_age, bool)
                or not isinstance(
                    max_age,
                    (int, float),
                )
            ):
                raise ValueError(
                    "location parameter max age must be a positive number"
                )

            if max_age <= 0:
                raise ValueError(
                    "location parameter max age must be greater than zero"
                )

        self._max_age_seconds = max_age_seconds
        self._max_age_by_parameter = (
            parameter_policy
        )
        self._max_age_by_location_parameter = (
            location_parameter_policy
        )

        self._clock = (
            clock
            if clock is not None
            else lambda: datetime.now(timezone.utc)
        )

        self._observations_by_location = {}

    def update(self, observations):
        observations = list(observations)

        if not observations:
            return []

        location_id = observations[0].location_id

        if any(
            observation.location_id != location_id
            for observation in observations
        ):
            raise ValueError(
                "observations must share location_id"
            )

        current = self._observations_by_location.setdefault(
            location_id,
            {},
        )

        self._remove_stale(
            location_id
        )

        current = self._observations_by_location.setdefault(
            location_id,
            {},
        )

        for observation in observations:
            current[observation.parameter] = observation

        return list(current.values())

    def locations(self):
        return list(
            self._observations_by_location.keys()
        )

    def snapshot(self):
        observations = []

        for location_id in self.locations():
            observations.extend(
                self.for_location(
                    location_id
                )
            )

        return observations

    def for_location(self, location_id):
        self._remove_stale(
            location_id
        )

        current = self._observations_by_location.get(
            location_id,
            {},
        )

        return list(current.values())

    def withdraw(
        self,
        location_id,
        parameter,
    ):
        current = (
            self._observations_by_location.get(
                location_id
            )
        )

        if current is None:
            return []

        current.pop(
            parameter,
            None,
        )

        return list(
            current.values()
        )

    def _remove_stale(
        self,
        location_id,
    ):
        current = self._observations_by_location.get(
            location_id
        )

        if not current:
            return

        stale_parameters = [
            parameter
            for parameter, observation
            in current.items()
            if self._is_stale(observation)
        ]

        for parameter in stale_parameters:
            del current[parameter]

    def _max_age_for(
        self,
        location_id,
        parameter,
    ):
        location_parameter_key = (
            location_id,
            parameter,
        )

        if (
            location_parameter_key
            in self._max_age_by_location_parameter
        ):
            return self._max_age_by_location_parameter[
                location_parameter_key
            ]

        if parameter in self._max_age_by_parameter:
            return self._max_age_by_parameter[
                parameter
            ]

        return self._max_age_seconds

    def _is_stale(
        self,
        observation,
    ):
        max_age_seconds = self._max_age_for(
            observation.location_id,
            observation.parameter,
        )

        if max_age_seconds is None:
            return False

        observed_at = datetime.fromisoformat(
            observation.observed_at
        )

        now = self._clock()

        age_seconds = (
            now - observed_at
        ).total_seconds()

        return (
            age_seconds
            > max_age_seconds
        )

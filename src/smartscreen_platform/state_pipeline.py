from __future__ import annotations


class PlatformStatePipeline:
    """Orchestrate observations into household state entries."""

    def __init__(
        self,
        *,
        household_state,
        interpreters,
        capabilities,
        knowledge=None,
    ):
        self._household_state = household_state
        self._interpreters = tuple(interpreters)
        self._capabilities = tuple(capabilities)
        self._knowledge = knowledge

    def process(
        self,
        observations,
        *,
        location_id=None,
    ):
        observations = list(observations)

        observations_by_location = {}

        for observation in observations:
            observations_by_location.setdefault(
                observation.location_id,
                [],
            ).append(observation)

        if (
            not observations
            and location_id is not None
        ):
            observations_by_location[
                location_id
            ] = []

        entries = []

        for (
            current_location_id,
            location_observations,
        ) in observations_by_location.items():
            interpretations = []

            for interpreter in self._interpreters:
                interpretations.extend(
                    interpreter.interpret(
                        location_observations,
                        knowledge=self._knowledge,
                    )
                )

            for capability in self._capabilities:
                patches = list(
                    capability.evaluate(
                        interpretations,
                        observations=location_observations,
                        knowledge=self._knowledge,
                    )
                )

                produced_targets = {
                    patch.target
                    for patch in patches
                }

                for patch in patches:
                    entries.append(
                        self._household_state.apply(patch)
                    )

                resolved_location_id = (
                    location_observations[0].location_id
                    if location_observations
                    else current_location_id
                )

                for target in getattr(
                    capability,
                    "managed_targets",
                    (),
                ):
                    if target in produced_targets:
                        continue

                    self._household_state.remove(
                        target,
                        location_id=resolved_location_id,
                    )

        return entries

from __future__ import annotations

import inspect
from typing import Any


class HomeAssistantStateEventConsumer:
    def __init__(
        self,
        provider,
        *,
        observation_adapter=None,
        observation_sink=None,
        observation_accumulator=None,
        device_data_ingestion=None,
        device_data_adapter=None,
    ) -> None:
        self._provider = provider
        self._observation_adapter = observation_adapter
        self._observation_sink = observation_sink
        self._observation_accumulator = (
            observation_accumulator
        )
        self._device_data_ingestion = (
            device_data_ingestion
        )
        self._device_data_adapter = (
            device_data_adapter
        )

    def consume(
        self,
        message: dict[str, Any],
    ) -> None:
        if message.get("type") != "event":
            return

        event = message.get("event")

        if not isinstance(event, dict):
            return

        if event.get("event_type") != "state_changed":
            return

        data = event.get("data")

        if not isinstance(data, dict):
            return

        entity_id = data.get("entity_id")

        if not isinstance(entity_id, str):
            return

        new_state = data.get("new_state")

        if (
            new_state is not None
            and not isinstance(new_state, dict)
        ):
            return

        # Preserve the existing Dashboard/Home Assistant path.
        self._provider.update_state(
            entity_id,
            new_state,
        )

        # Device Data is a migration-first semantic path.
        # When a mapped source produces a Canonical Observation,
        # use it directly and do not duplicate the event through
        # the legacy Observation adapter. Unmapped sources fall
        # back to the established path.
        device_data_observation = None

        if new_state is not None:
            raw_value = new_state.get(
                "state"
            )

            if (
                self._device_data_adapter
                is not None
            ):
                try:
                    device_data_observation = (
                        self._device_data_adapter.ingest_state(
                            entity_id=entity_id,
                            raw_state=new_state,
                        )
                    )
                except ValueError:
                    # Invalid or unmapped Device Data
                    # must not interrupt the legacy path.
                    device_data_observation = None

            elif (
                self._device_data_ingestion
                is not None
            ):
                available = raw_value not in {
                    None,
                    "unknown",
                    "unavailable",
                }

                try:
                    device_data_observation = (
                        self._device_data_ingestion.ingest(
                            adapter_id="home_assistant",
                            source_id=entity_id,
                            value=raw_value,
                            available=available,
                        )
                    )
                except ValueError:
                    # Backward-compatible migration hook.
                    device_data_observation = None

        # A removed entity has no current physical observation
        # to contribute to the platform state pipeline.
        if new_state is None:
            return

        if self._observation_sink is None:
            return

        # Canonical Device Data availability is semantic.
        # Normalize a mapped Device Data result into a batch so
        # single-parameter and composite sources share the same
        # availability handling.
        if device_data_observation is not None:
            if isinstance(
                device_data_observation,
                list,
            ):
                device_data_observations = list(
                    device_data_observation
                )
            else:
                device_data_observations = [
                    device_data_observation
                ]

            location_id = None
            available_observations = []
            observations_after_withdraw = None
            had_unavailable = False

            for observation in (
                device_data_observations
            ):
                observation_location_id = getattr(
                    observation,
                    "location_id",
                    None,
                )

                if (
                    location_id is None
                    and observation_location_id
                    is not None
                ):
                    location_id = (
                        observation_location_id
                    )

                if (
                    getattr(
                        observation,
                        "quality",
                        "good",
                    )
                    == "unavailable"
                ):
                    had_unavailable = True

                    parameter = getattr(
                        observation,
                        "parameter",
                        None,
                    )

                    if (
                        self._observation_accumulator
                        is not None
                        and observation_location_id
                        is not None
                        and parameter is not None
                    ):
                        observations_after_withdraw = (
                            self._observation_accumulator.withdraw(
                                observation_location_id,
                                parameter,
                            )
                        )

                    continue

                available_observations.append(
                    observation
                )

            if available_observations:
                observations = (
                    available_observations
                )

                if (
                    self._observation_accumulator
                    is not None
                ):
                    observations = (
                        self._observation_accumulator.update(
                            observations
                        )
                    )

            elif had_unavailable:
                observations = (
                    observations_after_withdraw
                    if observations_after_withdraw
                    is not None
                    else []
                )

            else:
                observations = []

        else:
            # Only the legacy fallback requires the legacy
            # Home Assistant Observation adapter.
            if self._observation_adapter is None:
                return

            observations = (
                self._observation_adapter.convert(
                    new_state
                )
            )

            if not observations:
                return

            first_observation = observations[0]
            location_id = getattr(
                first_observation,
                "location_id",
                None,
            )

            if (
                self._observation_accumulator
                is not None
            ):
                observations = (
                    self._observation_accumulator.update(
                        observations
                    )
                )

        process = self._observation_sink.process
        parameters = inspect.signature(
            process
        ).parameters

        supports_location_id = (
            "location_id" in parameters
            or any(
                parameter.kind
                == inspect.Parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )
        )

        if supports_location_id:
            process(
                observations,
                location_id=location_id,
            )
        else:
            process(
                observations
            )

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import parse_qs, urlsplit

from .dashboard import DASHBOARD_HTML
from .todo_store import TodoStore, TodoError
from .home_status import FileHomeStatusProvider
from .presentation import DashboardPresentationBuilder

STATIC_DIR = Path(__file__).parent / "static"


class SnapshotHost(Protocol):
    def snapshot(self) -> Any:
        """Return the current SmartScreenOS snapshot."""





class SnapshotApplication:
    """Minimal application for serving snapshots and explicit resident commands."""

    def __init__(
        self,
        host: SnapshotHost,
        *,
        photo_dir: str | Path | None = None,
        todo_file: str | Path | None = None,
        home_file: str | Path | None = None,
        home_provider=None,
        household_state_source=None,
        observation_source=None,
        presentation_builder=None,
        device_control_dispatcher=None,
        household_action_executor=None,
        device_state_refresher=None,
        device_definitions=None,
        device_parameter_store=None,
        device_power_dependency_resolver=None,
        calendar_event_service=None,
    ) -> None:
        self._host = host
        self._photo_dir = (
            Path(photo_dir).resolve()
            if photo_dir is not None
            else None
        )
        self._todo_file = (
            Path(todo_file).resolve()
            if todo_file is not None
            else None
        )
        self._household_state_source = household_state_source
        self._observation_source = observation_source
        self._device_control_dispatcher = (
            device_control_dispatcher
        )
        self._household_action_executor = (
            household_action_executor
        )
        self._device_state_refresher = (
            device_state_refresher
        )
        self._device_definitions = list(
            device_definitions or []
        )
        self._device_parameter_store = (
            device_parameter_store
        )
        self._device_power_dependency_resolver = (
            device_power_dependency_resolver
        )
        self._calendar_event_service = (
            calendar_event_service
        )
        self._presentation_builder = (
            presentation_builder
            if presentation_builder is not None
            else DashboardPresentationBuilder()
        )

        self._home_provider = (
            home_provider
            if home_provider is not None
            else (
                FileHomeStatusProvider(
                    Path(home_file).resolve()
                )
                if home_file is not None
                else None
            )
        )

    def handle(
        self,
        *,
        method: str,
        path: str,
        body: bytes = b"",
    ) -> tuple[int, dict[str, str], bytes]:
        if path == "/api/dashboard":
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                        "Allow": "GET",
                    },
                    self._json_body(
                        {
                            "error": "method not allowed",
                        }
                    ),
                )

            household_states = (
                self._household_state_source.snapshot()
                if self._household_state_source is not None
                else []
            )

            observations = (
                self._observation_source.snapshot()
                if self._observation_source is not None
                else []
            )

            view = self._presentation_builder.build(
                household_states=household_states,
                observations=observations,
            )

            payload = view.to_dict()

            if (
                self._device_parameter_store
                is not None
            ):
                payload[
                    "device_states"
                ] = [
                    {
                        "device_id":
                            entry.device_id,
                        "parameter":
                            entry.parameter,
                        "value":
                            entry.value,
                        "available":
                            entry.available,
                    }
                    for entry
                    in (
                        self._device_parameter_store
                        .snapshot()
                    )
                ]

            controllable_devices = []

            for device in self._device_definitions:
                controls = (
                    device.controls or {}
                )

                if (
                    not controls
                    and not device.area_readonly
                ):
                    continue

                projected_controls = []

                for control in controls.values():
                    projected_control = {
                        "control_id": (
                            control.control_id
                        ),
                        "kind": (
                            control.kind
                        ),
                        "parameter": (
                            control.parameter
                        ),
                        "options": list(
                            control.options
                        ),
                    }

                    if control.minimum is not None:
                        projected_control[
                            "min"
                        ] = control.minimum

                    if control.maximum is not None:
                        projected_control[
                            "max"
                        ] = control.maximum

                    if control.step is not None:
                        projected_control[
                            "step"
                        ] = control.step

                    projected_controls.append(
                        projected_control
                    )

                projected_device = {
                    "device_id": (
                        device.device_id
                    ),
                    "name": device.name,
                    "location_id": (
                        device.location_id
                    ),
                    "controls": (
                        projected_controls
                    ),
                }

                if device.area_readonly:
                    projected_device[
                        "area_readonly"
                    ] = True

                if device.device_type is not None:
                    projected_device[
                        "device_type"
                    ] = device.device_type

                if (
                    device.power_source_device_id
                    is not None
                ):
                    projected_device[
                        "power_source_device_id"
                    ] = (
                        device.power_source_device_id
                    )

                if (
                    device.power_control_device_id
                    is not None
                ):
                    projected_device[
                        "power_control_device_id"
                    ] = (
                        device.power_control_device_id
                    )

                if (
                    self._device_power_dependency_resolver
                    is not None
                    and "power" in device.parameters
                ):
                    availability_reason = (
                        self._device_power_dependency_resolver
                        .resolve(
                            device_id=device.device_id,
                            parameter="power",
                        )
                    )

                    if (
                        availability_reason
                        == "powered_off_by_upstream"
                    ):
                        projected_device[
                            "availability_reason"
                        ] = availability_reason

                controllable_devices.append(
                    projected_device
                )

            if controllable_devices:
                payload[
                    "devices"
                ] = controllable_devices

            return (
                200,
                {
                    "Content-Type": "application/json; charset=utf-8",
                },
                self._json_body(payload),
            )

        if path == "/api/household/actions":
            if method != "POST":
                return (
                    405,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                        "Allow": "POST",
                    },
                    self._json_body(
                        {
                            "error": (
                                "method not allowed"
                            ),
                        }
                    ),
                )

            try:
                payload = json.loads(
                    body.decode("utf-8")
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ):
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": "invalid json",
                        }
                    ),
                )

            if not isinstance(
                payload,
                dict,
            ):
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": (
                                "invalid payload"
                            ),
                        }
                    ),
                )

            action_id = payload.get(
                "action_id"
            )

            if (
                not isinstance(
                    action_id,
                    str,
                )
                or not action_id
            ):
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error":
                                "action_id required",
                        }
                    ),
                )

            if (
                self._household_action_executor
                is None
            ):
                return (
                    503,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": (
                                "household action executor "
                                "unavailable"
                            ),
                        }
                    ),
                )

            try:
                result = (
                    self._household_action_executor
                    .execute(
                        action_id
                    )
                )
            except ValueError as exc:
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": str(exc),
                        }
                    ),
                )

            return (
                200,
                {
                    "Content-Type": (
                        "application/json; "
                        "charset=utf-8"
                    ),
                },
                self._json_body(result),
            )

        if path == "/api/device/actions":
            if method != "POST":
                return (
                    405,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                        "Allow": "POST",
                    },
                    self._json_body(
                        {
                            "error": (
                                "method not allowed"
                            ),
                        }
                    ),
                )

            try:
                payload = json.loads(
                    body.decode("utf-8")
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ):
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": "invalid json",
                        }
                    ),
                )

            if not isinstance(
                payload,
                dict,
            ):
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": (
                                "invalid payload"
                            ),
                        }
                    ),
                )

            device_id = payload.get(
                "device_id"
            )
            control_id = payload.get(
                "control_id"
            )

            if (
                not isinstance(
                    device_id,
                    str,
                )
                or not device_id
                or not isinstance(
                    control_id,
                    str,
                )
                or not control_id
            ):
                return (
                    400,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": (
                                "device_id and "
                                "control_id required"
                            ),
                        }
                    ),
                )

            if (
                self._device_control_dispatcher
                is None
            ):
                return (
                    503,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": (
                                "device control "
                                "dispatcher unavailable"
                            ),
                        }
                    ),
                )

            if (
                self._device_power_dependency_resolver
                is not None
            ):
                availability_reason = (
                    self._device_power_dependency_resolver
                    .resolve(
                        device_id=device_id,
                        parameter="power",
                    )
                )

                if (
                    availability_reason
                    == "powered_off_by_upstream"
                ):
                    return (
                        403,
                        {
                            "Content-Type": (
                                "application/json; "
                                "charset=utf-8"
                            ),
                        },
                        self._json_body(
                            {
                                "error": (
                                    "powered_off_by_upstream"
                                ),
                            }
                        ),
                    )

            try:
                result = (
                    self._device_control_dispatcher
                    .execute(
                        device_id=device_id,
                        control_id=control_id,
                        value=payload.get(
                            "value"
                        ),
                    )
                )

            except ValueError as exc:
                return (
                    403,
                    {
                        "Content-Type": (
                            "application/json; "
                            "charset=utf-8"
                        ),
                    },
                    self._json_body(
                        {
                            "error": str(exc),
                        }
                    ),
                )

            if (
                self._device_state_refresher
                is not None
            ):
                try:
                    (
                        self._device_state_refresher
                        .refresh()
                    )
                except Exception:
                    # Command succeeded. Background
                    # polling remains the fallback
                    # if confirmation fails.
                    pass

            return (
                200,
                {
                    "Content-Type": (
                        "application/json; "
                        "charset=utf-8"
                    ),
                },
                self._json_body(
                    {
                        "result": result,
                    }
                ),
            )

        if path == "/api/home/actions":
            if method != "POST":
                return (
                    405,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                        "Allow": "POST",
                    },
                    self._json_body(
                        {
                            "error": "method not allowed",
                        }
                    ),
                )

            try:
                payload = json.loads(
                    body.decode("utf-8")
                )
            except (
                UnicodeDecodeError,
                json.JSONDecodeError,
            ):
                return (
                    400,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "invalid json",
                        }
                    ),
                )

            if not isinstance(payload, dict):
                return (
                    400,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "invalid payload",
                        }
                    ),
                )

            entity_id = payload.get("entity_id")
            action = payload.get("action")

            if (
                not isinstance(entity_id, str)
                or not entity_id
                or not isinstance(action, str)
                or not action
            ):
                return (
                    400,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "entity_id and action required",
                        }
                    ),
                )

            if self._home_provider is None:
                return (
                    503,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "home provider unavailable",
                        }
                    ),
                )

            try:
                if action == "set_temperature":
                    temperature = payload.get(
                        "temperature"
                    )

                    if (
                        not isinstance(
                            temperature,
                            (int, float),
                        )
                        or isinstance(
                            temperature,
                            bool,
                        )
                    ):
                        return (
                            400,
                            {
                                "Content-Type": "application/json; charset=utf-8",
                            },
                            self._json_body(
                                {
                                    "error": "numeric temperature required",
                                }
                            ),
                        )

                    result = self._home_provider.set_temperature(
                        entity_id,
                        temperature,
                    )

                elif action == "set_fan_mode":
                    fan_mode = payload.get(
                        "fan_mode"
                    )

                    if (
                        not isinstance(
                            fan_mode,
                            str,
                        )
                        or not fan_mode
                    ):
                        return (
                            400,
                            {
                                "Content-Type": "application/json; charset=utf-8",
                            },
                            self._json_body(
                                {
                                    "error": "fan_mode required",
                                }
                            ),
                        )

                    result = self._home_provider.set_fan_mode(
                        entity_id,
                        fan_mode,
                    )

                elif action == "set_hvac_mode":
                    hvac_mode = payload.get(
                        "hvac_mode"
                    )

                    if (
                        not isinstance(
                            hvac_mode,
                            str,
                        )
                        or not hvac_mode
                    ):
                        return (
                            400,
                            {
                                "Content-Type": "application/json; charset=utf-8",
                            },
                            self._json_body(
                                {
                                    "error": "hvac_mode required",
                                }
                            ),
                        )

                    result = self._home_provider.set_hvac_mode(
                        entity_id,
                        hvac_mode,
                    )

                elif action == "cover_action":
                    cover_action = payload.get(
                        "cover_action"
                    )

                    if (
                        not isinstance(
                            cover_action,
                            str,
                        )
                        or not cover_action
                    ):
                        return (
                            400,
                            {
                                "Content-Type": "application/json; charset=utf-8",
                            },
                            self._json_body(
                                {
                                    "error": "cover_action required",
                                }
                            ),
                        )

                    result = (
                        self._home_provider.perform_cover_action(
                            entity_id,
                            cover_action,
                        )
                    )

                else:
                    result = self._home_provider.perform_action(
                        entity_id,
                        action,
                    )
            except ValueError as exc:
                return (
                    403,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": str(exc),
                        }
                    ),
                )

            return (
                200,
                {
                    "Content-Type": "application/json; charset=utf-8",
                },
                self._json_body(result),
            )

        if (
            path == "/api/home/events"
            or path.startswith("/api/home/events?")
        ):
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": (
                            "text/event-stream; charset=utf-8"
                        ),
                        "Allow": "GET",
                    },
                    b"",
                )

            return (
                200,
                {
                    "Content-Type": (
                        "text/event-stream; charset=utf-8"
                    ),
                    "Cache-Control": "no-cache",
                },
                b"",
            )

        if path == "/api/home" or path.startswith("/api/home?"):
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                        "Allow": "GET",
                    },
                    self._json_body(
                        {
                            "error": "method not allowed",
                        }
                    ),
                )

            items = (
                self._home_provider.get_items()
                if self._home_provider is not None
                else []
            )

            payload = {
                "items": items,
            }

            if (
                self._home_provider is not None
                and hasattr(
                    self._home_provider,
                    "revision",
                )
            ):
                payload["revision"] = (
                    self._home_provider.revision
                )

            if (
                self._home_provider is not None
                and hasattr(
                    self._home_provider,
                    "available",
                )
            ):
                payload["available"] = (
                    self._home_provider.available
                )

            return (
                200,
                {
                    "Content-Type": "application/json; charset=utf-8",
                },
                self._json_body(
                    payload
                ),
            )

        if (
            path == "/api/calendar"
            or path.startswith("/api/calendar?")
        ):
            headers = {
                "Cache-Control": "no-store",
                "Content-Type": (
                    "application/json; charset=utf-8"
                ),
            }

            if method != "GET":
                return (
                    405,
                    {
                        **headers,
                        "Allow": "GET",
                    },
                    self._json_body(
                        {
                            "error": "method not allowed",
                        }
                    ),
                )

            if self._calendar_event_service is None:
                return (
                    503,
                    headers,
                    self._json_body(
                        {
                            "error": (
                                "calendar service unavailable"
                            ),
                        }
                    ),
                )

            query = parse_qs(
                urlsplit(path).query,
                keep_blank_values=True,
            )

            start_values = query.get("start", [])
            end_values = query.get("end", [])

            if (
                len(start_values) != 1
                or len(end_values) != 1
            ):
                return (
                    400,
                    headers,
                    self._json_body(
                        {
                            "error": (
                                "start and end required"
                            ),
                        }
                    ),
                )

            try:
                start = datetime.fromisoformat(
                    start_values[0]
                )
                end = datetime.fromisoformat(
                    end_values[0]
                )
            except ValueError:
                return (
                    400,
                    headers,
                    self._json_body(
                        {
                            "error": (
                                "invalid calendar range"
                            ),
                        }
                    ),
                )

            if (start.tzinfo is None) != (end.tzinfo is None) or end < start:
                return (
                    400,
                    headers,
                    self._json_body(
                        {
                            "error": (
                                "invalid calendar range"
                            ),
                        }
                    ),
                )

            from .calendar_source import CalendarSourceError, CalendarSyncPending

            try:
                status_details = None
                details = getattr(self._calendar_event_service, "snapshot_details", None)
                snapshot = getattr(self._calendar_event_service, "snapshot", None)
                if details is not None:
                    events, status_details = details(start=start, end=end)
                    stale = bool(status_details and status_details["stale"])
                elif snapshot is None:
                    events = self._calendar_event_service.list_events(start=start, end=end)
                    stale = False
                else:
                    events, stale = snapshot(start=start, end=end)
            except CalendarSyncPending as error:
                headers = dict(headers, **{'Retry-After': str(error.retry_after),
                                            'X-Calendar-State': error.status['state']})
                return 503, headers, self._json_body({'error': 'calendar service unavailable',
                                                      'calendar_status': error.status})
            except CalendarSourceError:
                return 503, headers, self._json_body({"error": "calendar service unavailable"})
            except ValueError:
                return 400, headers, self._json_body({"error": "invalid calendar range"})
            if stale:
                headers = dict(headers, **{"X-Calendar-Stale": "true"})
            if status_details and "age_seconds" in status_details:
                headers["X-Calendar-Age-Seconds"] = str(status_details["age_seconds"])

            return (
                200,
                headers,
                self._json_body(
                    {
                        **({"calendar_status": status_details} if status_details else {}),
                        "events": [
                            {
                                "event_id": event.event_id,
                                "calendar_id": (
                                    event.calendar_id
                                ),
                                "title": event.title,
                                "start": (
                                    event.start.isoformat()
                                ),
                                "end": event.end.isoformat(),
                                "all_day": event.all_day,
                            }
                            for event in events
                        ],
                    }
                ),
            )

        if path == "/api/todos":
            headers = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
            if method not in ("GET", "POST"):
                return 405, dict(headers, Allow="GET, POST"), self._json_body({"error": "method not allowed"})
            try:
                store = TodoStore(self._todo_file)
                if method == "GET":
                    result = store.read()
                else:
                    if len(body) > 4096:
                        raise TodoError(413, "request_too_large")
                    try:
                        payload = json.loads(body.decode("utf-8"))
                    except (UnicodeError, ValueError):
                        raise TodoError(400, "invalid_json") from None
                    result = store.mutate(payload)
                return 200, headers, self._json_body(result)
            except TodoError as exc:
                return exc.status, headers, self._json_body({"error": exc.code})

        if path == "/api/photos":
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                        "Allow": "GET",
                    },
                    self._json_body(
                        {
                            "error": "method not allowed",
                        }
                    ),
                )

            photos = []

            if self._photo_dir is not None and self._photo_dir.is_dir():
                supported_suffixes = {
                    ".jpg",
                    ".jpeg",
                    ".png",
                }

                for candidate in sorted(
                    self._photo_dir.iterdir(),
                    key=lambda item: item.name,
                ):
                    if not candidate.is_file():
                        continue

                    if candidate.suffix.lower() not in supported_suffixes:
                        continue

                    photos.append(
                        {
                            "name": candidate.name,
                            "url": "/photos/" + candidate.name,
                        }
                    )

            return (
                200,
                {
                    "Content-Type": "application/json; charset=utf-8",
                },
                self._json_body(
                    {
                        "photos": photos,
                    }
                ),
            )

        if path.startswith("/photos/"):
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                        "Allow": "GET",
                    },
                    self._json_body(
                        {
                            "error": "method not allowed",
                        }
                    ),
                )

            if self._photo_dir is None:
                return (
                    404,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "not found",
                        }
                    ),
                )

            relative_name = path[len("/photos/"):]

            if not relative_name:
                return (
                    404,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "not found",
                        }
                    ),
                )

            candidate = (
                self._photo_dir / relative_name
            ).resolve()

            try:
                candidate.relative_to(self._photo_dir)
            except ValueError:
                return (
                    404,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "not found",
                        }
                    ),
                )

            if not candidate.is_file():
                return (
                    404,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "not found",
                        }
                    ),
                )

            suffix = candidate.suffix.lower()

            content_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
            }

            content_type = content_types.get(suffix)

            if content_type is None:
                return (
                    404,
                    {
                        "Content-Type": "application/json; charset=utf-8",
                    },
                    self._json_body(
                        {
                            "error": "not found",
                        }
                    ),
                )

            return (
                200,
                {
                    "Content-Type": content_type,
                },
                candidate.read_bytes(),
            )

        if path == "/static/dashboard.css" or path.startswith("/static/dashboard.css?"):
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "text/css; charset=utf-8",
                        "Allow": "GET",
                    },
                    b"",
                )

            return (
                200,
                {
                    "Content-Type": "text/css; charset=utf-8",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                (STATIC_DIR / "dashboard.css").read_bytes(),
            )

        if path == "/static/dashboard.js" or path.startswith("/static/dashboard.js?"):
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "application/javascript; charset=utf-8",
                        "Allow": "GET",
                    },
                    b"",
                )

            return (
                200,
                {
                    "Content-Type": "application/javascript; charset=utf-8",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                (STATIC_DIR / "dashboard.js").read_bytes(),
            )

        if path == "/" or path.startswith("/?"):
            if method != "GET":
                return (
                    405,
                    {
                        "Content-Type": "text/html; charset=utf-8",
                        "Allow": "GET",
                    },
                    b"",
                )

            return (
                200,
                {
                    "Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                DASHBOARD_HTML,
            )

        if path != "/api/snapshot":
            return (
                404,
                {
                    "Content-Type": (
                        "application/json; charset=utf-8"
                    )
                },
                self._json_body(
                    {
                        "error": "not found",
                    }
                ),
            )

        if method != "GET":
            return (
                405,
                {
                    "Content-Type": (
                        "application/json; charset=utf-8"
                    ),
                    "Allow": "GET",
                },
                self._json_body(
                    {
                        "error": "method not allowed",
                    }
                ),
            )

        return (
            200,
            {
                "Content-Type": (
                    "application/json; charset=utf-8"
                )
            },
            self._json_body(self._host.snapshot()),
        )

    @staticmethod
    def _json_body(payload: Any) -> bytes:
        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")


from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def create_http_server(
    app: SnapshotApplication,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    home_status_notifier=None,
    dashboard_state_notifier=None,
) -> ThreadingHTTPServer:
    class SnapshotRequestHandler(BaseHTTPRequestHandler):
        def _handle_request(self) -> None:
            if (
                self.command == "GET"
                and (
                    self.path == "/api/home/events"
                    or self.path.startswith(
                        "/api/home/events?"
                    )
                )
                and home_status_notifier is not None
            ):
                self._handle_home_status_events()
                return

            if (
                self.command == "GET"
                and (
                    self.path == "/api/dashboard/events"
                    or self.path.startswith(
                        "/api/dashboard/events?"
                    )
                )
                and dashboard_state_notifier is not None
            ):
                self._handle_dashboard_state_events()
                return

            if self.command == "POST" and self.path == "/api/todos":
                from urllib.parse import urlsplit
                origin = self.headers.get("Origin")
                try:
                    valid_origin = not origin or urlsplit(origin).netloc == self.headers.get("Host")
                except ValueError:
                    valid_origin = False
                content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = -1
                if not valid_origin:
                    self.close_connection = True
                    self.send_error(403)
                    return
                if content_type != "application/json" or length <= 0:
                    self.close_connection = True
                    self.send_error(400)
                    return
                if length > 4096:
                    self.close_connection = True
                    self.send_error(413)
                    return

            request_body = b""

            if self.command == "POST":
                content_length = self.headers.get(
                    "Content-Length"
                )

                if content_length:
                    try:
                        length = int(content_length)
                    except ValueError:
                        length = 0

                    if length > 0:
                        request_body = self.rfile.read(
                            length
                        )

            status, headers, body = app.handle(
                method=self.command,
                path=self.path,
                body=request_body,
            )

            self.send_response(status)

            for name, value in headers.items():
                self.send_header(name, value)

            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()

            if body:
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    return

        def _handle_home_status_events(
            self,
        ) -> None:
            revision = (
                home_status_notifier.revision
            )

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/event-stream; charset=utf-8",
            )
            self.send_header(
                "Cache-Control",
                "no-cache",
            )
            self.end_headers()

            while True:
                next_revision = (
                    home_status_notifier.wait_for_change(
                        revision,
                        timeout=30.0,
                    )
                )

                if next_revision == revision:
                    continue

                payload = json.dumps(
                    {
                        "revision": next_revision,
                    },
                    separators=(",", ":"),
                )

                event = (
                    "event: home-status-changed\n"
                    f"data: {payload}\n"
                    "\n"
                ).encode("utf-8")

                try:
                    self.wfile.write(event)
                    self.wfile.flush()
                except (
                    BrokenPipeError,
                    ConnectionResetError,
                ):
                    return

                revision = next_revision

        def _handle_dashboard_state_events(
            self,
        ) -> None:
            revision = (
                dashboard_state_notifier.revision
            )

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/event-stream; charset=utf-8",
            )
            self.send_header(
                "Cache-Control",
                "no-cache",
            )
            self.end_headers()

            while True:
                next_revision = (
                    dashboard_state_notifier.wait_for_change(
                        revision,
                        timeout=30.0,
                    )
                )

                if next_revision == revision:
                    continue

                payload = json.dumps(
                    {
                        "revision": next_revision,
                    },
                    separators=(",", ":"),
                )

                event = (
                    "event: dashboard-state-changed\n"
                    f"data: {payload}\n"
                    "\n"
                ).encode("utf-8")

                try:
                    self.wfile.write(event)
                    self.wfile.flush()
                except (
                    BrokenPipeError,
                    ConnectionResetError,
                ):
                    return

                revision = next_revision

        def do_GET(self) -> None:
            self._handle_request()

        def do_POST(self) -> None:
            self._handle_request()

        def log_message(
            self,
            format: str,
            *args,
        ) -> None:
            # Keep tests and local display output quiet for now.
            return

    return ThreadingHTTPServer(
        (host, port),
        SnapshotRequestHandler,
    )

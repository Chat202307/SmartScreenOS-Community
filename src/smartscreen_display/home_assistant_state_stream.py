from __future__ import annotations

import json
import threading
from typing import Any

from websockets.sync.client import connect


class HomeAssistantStateStream:
    def __init__(
        self,
        *,
        token: str,
        consumer,
        base_url: str | None = None,
        connector=connect,
    ) -> None:
        self._token = token
        self._consumer = consumer
        self._base_url = base_url
        self._connector = connector
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._connection = None

    def start(self) -> None:
        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_background,
            name="smartscreen-ha-state-stream",
            daemon=False,
        )

        self._thread.start()

    def _run_background(self) -> None:
        try:
            self.run_forever()
        except Exception:
            if not self._stop_event.is_set():
                raise

    def stop(self) -> None:
        self._stop_event.set()

        connection = self._connection

        if connection is not None:
            connection.close()

    def is_alive(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
        )

    def join(
        self,
        timeout: float | None = None,
    ) -> None:
        if self._thread is None:
            return

        self._thread.join(
            timeout=timeout
        )

    def run_forever(
        self,
        *,
        reconnect_delay: float = 5.0,
    ) -> None:
        while not self._stop_event.is_set():
            try:
                self.run()
            except Exception:
                if self._stop_event.is_set():
                    return

            if self._stop_event.is_set():
                return

            if reconnect_delay > 0:
                if self._stop_event.wait(
                    timeout=reconnect_delay
                ):
                    return

    def run(
        self,
        *,
        max_events: int | None = None,
    ) -> None:
        if self._base_url is None:
            raise ValueError(
                "Home Assistant base URL required"
            )

        websocket_url = self._websocket_url(
            self._base_url
        )

        with self._connector(
            websocket_url,
            proxy=None,
        ) as connection:
            self._connection = connection

            try:
                self.run_connection(
                    connection,
                    max_events=max_events,
                )
            finally:
                self._connection = None

    @staticmethod
    def _websocket_url(
        base_url: str,
    ) -> str:
        base_url = base_url.rstrip("/")

        if base_url.startswith("https://"):
            return (
                "wss://"
                + base_url[len("https://"):]
                + "/api/websocket"
            )

        if base_url.startswith("http://"):
            return (
                "ws://"
                + base_url[len("http://"):]
                + "/api/websocket"
            )

        raise ValueError(
            "Home Assistant URL must use "
            "http or https"
        )

    def run_connection(
        self,
        connection,
        *,
        max_events: int | None = None,
    ) -> None:
        auth_required = self._receive_json(
            connection
        )

        if auth_required.get("type") != "auth_required":
            raise ValueError(
                "auth_required expected"
            )

        connection.send(
            json.dumps(
                {
                    "type": "auth",
                    "access_token": self._token,
                }
            )
        )

        auth_result = self._receive_json(
            connection
        )

        if auth_result.get("type") != "auth_ok":
            raise ValueError(
                "Home Assistant authentication failed"
            )

        connection.send(
            json.dumps(
                {
                    "id": 1,
                    "type": "subscribe_events",
                    "event_type": "state_changed",
                }
            )
        )

        subscription_result = self._receive_json(
            connection
        )

        if (
            subscription_result.get("type")
            != "result"
            or subscription_result.get("id") != 1
            or subscription_result.get("success")
            is not True
        ):
            raise ValueError(
                "state_changed subscription failed"
            )

        connection.send(
            json.dumps(
                {
                    "id": 2,
                    "type": "get_states",
                }
            )
        )

        pending_events = []

        while True:
            message = self._receive_json(
                connection
            )

            if (
                message.get("type") == "result"
                and message.get("id") == 2
            ):
                if (
                    message.get("success")
                    is not True
                ):
                    raise ValueError(
                        "get_states failed"
                    )

                states = message.get(
                    "result"
                )

                if not isinstance(states, list):
                    raise ValueError(
                        "invalid get_states result"
                    )

                break

            if message.get("type") == "event":
                pending_events.append(
                    message
                )

        for state in states:
            if not isinstance(state, dict):
                continue

            entity_id = state.get(
                "entity_id"
            )

            if not isinstance(
                entity_id,
                str,
            ):
                continue

            self._consumer.consume(
                {
                    "type": "event",
                    "event": {
                        "event_type":
                            "state_changed",
                        "data": {
                            "entity_id":
                                entity_id,
                            "new_state":
                                state,
                        },
                    },
                }
            )

        events_received = 0

        for message in pending_events:
            self._consumer.consume(
                message
            )
            events_received += 1

        while (
            max_events is None
            or events_received < max_events
        ):
            message = self._receive_json(
                connection
            )

            self._consumer.consume(
                message
            )

            if message.get("type") == "event":
                events_received += 1

    @staticmethod
    def _receive_json(
        connection,
    ) -> dict[str, Any]:
        message = connection.recv()

        if isinstance(message, bytes):
            message = message.decode("utf-8")

        payload = json.loads(message)

        if not isinstance(payload, dict):
            raise ValueError(
                "invalid Home Assistant message"
            )

        return payload

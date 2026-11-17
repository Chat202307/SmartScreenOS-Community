from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen


class HomeAssistantClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 5.0,
        opener=urlopen,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._opener = opener

    def get_json(self, path: str) -> Any:
        url = (
            self._base_url
            + "/"
            + path.lstrip("/")
        )

        request = Request(
            url,
            headers={
                "Authorization": "Bearer " + self._token,
                "Accept": "application/json",
            },
            method="GET",
        )

        with self._opener(
            request,
            timeout=self._timeout,
        ) as response:
            body = response.read()

        return json.loads(
            body.decode("utf-8")
        )


    def call_service(
        self,
        domain: str,
        service: str,
        entity_id: str,
        *,
        service_data: dict[str, Any] | None = None,
    ) -> Any:
        path = (
            "/api/services/"
            + domain
            + "/"
            + service
        )

        payload = {
            "entity_id": entity_id,
        }

        if service_data:
            payload.update(
                service_data
            )

        return self.post_json(
            path,
            payload,
        )

    def post_json(
        self,
        path: str,
        payload: Any,
    ) -> Any:
        url = (
            self._base_url
            + "/"
            + path.lstrip("/")
        )

        data = json.dumps(
            payload
        ).encode("utf-8")

        request = Request(
            url,
            data=data,
            headers={
                "Authorization": "Bearer " + self._token,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with self._opener(
            request,
            timeout=self._timeout,
        ) as response:
            body = response.read()

        return json.loads(
            body.decode("utf-8")
        )

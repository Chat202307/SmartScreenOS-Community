import json

from src.smartscreen_display.home_assistant_client import (
    HomeAssistantClient,
)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(
            self._payload
        ).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeUrlOpen:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(
            {
                "request": request,
                "timeout": timeout,
            }
        )
        return FakeResponse(self.payload)


def test_home_assistant_client_get_json():
    opener = FakeUrlOpen(
        [
            {
                "entity_id": "light.living_room",
                "state": "off",
            }
        ]
    )

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    payload = client.get_json("/api/states")

    assert payload == [
        {
            "entity_id": "light.living_room",
            "state": "off",
        }
    ]


def test_home_assistant_client_builds_url():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123/",
        "secret-token",
        opener=opener,
    )

    client.get_json("/api/states")

    request = opener.requests[0]["request"]

    assert request.full_url == (
        "http://localhost:8123/api/states"
    )


def test_home_assistant_client_sends_bearer_token():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.get_json("/api/states")

    request = opener.requests[0]["request"]

    assert (
        request.get_header("Authorization")
        == "Bearer secret-token"
    )


def test_home_assistant_client_requests_json():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.get_json("/api/states")

    request = opener.requests[0]["request"]

    assert (
        request.get_header("Accept")
        == "application/json"
    )


def test_home_assistant_client_uses_timeout():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        timeout=7.5,
        opener=opener,
    )

    client.get_json("/api/states")

    assert opener.requests[0]["timeout"] == 7.5


def test_home_assistant_client_post_json():
    opener = FakeUrlOpen(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
            }
        ]
    )

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    payload = client.post_json(
        "/api/services/light/toggle",
        {
            "entity_id": "light.living_room",
        },
    )

    assert payload == [
        {
            "entity_id": "light.living_room",
            "state": "on",
        }
    ]


def test_home_assistant_client_post_uses_post_method():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.post_json(
        "/api/services/light/toggle",
        {
            "entity_id": "light.living_room",
        },
    )

    request = opener.requests[0]["request"]

    assert request.get_method() == "POST"


def test_home_assistant_client_post_sends_json_body():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.post_json(
        "/api/services/light/toggle",
        {
            "entity_id": "light.living_room",
        },
    )

    request = opener.requests[0]["request"]

    assert json.loads(
        request.data.decode("utf-8")
    ) == {
        "entity_id": "light.living_room",
    }


def test_home_assistant_client_post_sets_content_type():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.post_json(
        "/api/services/light/toggle",
        {
            "entity_id": "light.living_room",
        },
    )

    request = opener.requests[0]["request"]

    assert (
        request.get_header("Content-type")
        == "application/json"
    )


def test_home_assistant_client_post_keeps_auth_header():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.post_json(
        "/api/services/light/toggle",
        {
            "entity_id": "light.living_room",
        },
    )

    request = opener.requests[0]["request"]

    assert (
        request.get_header("Authorization")
        == "Bearer secret-token"
    )


def test_home_assistant_client_post_uses_timeout():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        timeout=7.5,
        opener=opener,
    )

    client.post_json(
        "/api/services/light/toggle",
        {
            "entity_id": "light.living_room",
        },
    )

    assert opener.requests[0]["timeout"] == 7.5


def test_home_assistant_client_call_service():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.call_service(
        "light",
        "toggle",
        "light.living_room",
    )

    request = opener.requests[0]["request"]

    assert request.full_url == (
        "http://localhost:8123"
        "/api/services/light/toggle"
    )

    assert request.get_method() == "POST"

    assert json.loads(
        request.data.decode("utf-8")
    ) == {
        "entity_id": "light.living_room",
    }


def test_home_assistant_client_call_service_returns_response():
    opener = FakeUrlOpen(
        [
            {
                "entity_id": "light.living_room",
                "state": "on",
            }
        ]
    )

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    payload = client.call_service(
        "light",
        "toggle",
        "light.living_room",
    )

    assert payload == [
        {
            "entity_id": "light.living_room",
            "state": "on",
        }
    ]


def test_home_assistant_client_call_service_accepts_service_data():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.call_service(
        "climate",
        "set_temperature",
        "climate.living_room",
        service_data={
            "temperature": 24,
        },
    )

    request = opener.requests[0]["request"]

    assert request.full_url == (
        "http://localhost:8123"
        "/api/services/climate/set_temperature"
    )

    assert json.loads(
        request.data.decode("utf-8")
    ) == {
        "entity_id": "climate.living_room",
        "temperature": 24,
    }


def test_home_assistant_client_call_service_without_service_data_is_unchanged():
    opener = FakeUrlOpen([])

    client = HomeAssistantClient(
        "http://localhost:8123",
        "secret-token",
        opener=opener,
    )

    client.call_service(
        "light",
        "toggle",
        "light.living_room",
    )

    request = opener.requests[0]["request"]

    assert json.loads(
        request.data.decode("utf-8")
    ) == {
        "entity_id": "light.living_room",
    }

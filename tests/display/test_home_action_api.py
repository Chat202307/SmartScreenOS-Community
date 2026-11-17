import json

from src.smartscreen_display.server import SnapshotApplication


class FakeHost:
    def snapshot(self):
        return {
            "capabilities": {},
        }


class FakeHomeProvider:
    def __init__(self):
        self.actions = []

    def get_items(self):
        return []

    def perform_action(
        self,
        entity_id,
        action,
    ):
        self.actions.append(
            {
                "entity_id": entity_id,
                "action": action,
            }
        )

        return {
            "ok": True,
        }


def create_app(provider):
    return SnapshotApplication(
        FakeHost(),
        home_provider=provider,
    )


def test_home_action_api_performs_action():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "light.living_room",
                "action": "toggle",
            }
        ).encode("utf-8"),
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload == {
        "ok": True,
    }

    assert provider.actions == [
        {
            "entity_id": "light.living_room",
            "action": "toggle",
        }
    ]


def test_home_action_api_requires_post():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="GET",
        path="/api/home/actions",
    )

    assert status == 405
    assert headers["Allow"] == "POST"


def test_home_action_api_rejects_invalid_json():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=b"{invalid",
    )

    assert status == 400


def test_home_action_api_requires_entity_id():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "action": "toggle",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_requires_action():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "light.living_room",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_rejects_disallowed_action():
    class RejectingProvider(FakeHomeProvider):
        def perform_action(
            self,
            entity_id,
            action,
        ):
            raise ValueError(
                "action not allowed"
            )

    app = create_app(
        RejectingProvider()
    )

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "light.living_room",
                "action": "turn_on",
            }
        ).encode("utf-8"),
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 403
    assert payload == {
        "error": "action not allowed",
    }


def test_home_action_api_rejects_unknown_entity():
    class RejectingProvider(FakeHomeProvider):
        def perform_action(
            self,
            entity_id,
            action,
        ):
            raise ValueError(
                "action not allowed"
            )

    app = create_app(
        RejectingProvider()
    )

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "light.unknown",
                "action": "toggle",
            }
        ).encode("utf-8"),
    )

    assert status == 403


def test_home_action_api_sets_temperature():
    class TemperatureProvider(FakeHomeProvider):
        def __init__(self):
            super().__init__()
            self.temperature_calls = []

        def set_temperature(
            self,
            entity_id,
            temperature,
        ):
            self.temperature_calls.append(
                {
                    "entity_id": entity_id,
                    "temperature": temperature,
                }
            )

            return {
                "ok": True,
            }

    provider = TemperatureProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_temperature",
                "temperature": 24,
            }
        ).encode("utf-8"),
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload == {
        "ok": True,
    }

    assert provider.temperature_calls == [
        {
            "entity_id": "climate.living_room",
            "temperature": 24,
        }
    ]


def test_home_action_api_requires_temperature_for_set_temperature():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_temperature",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_rejects_non_numeric_temperature():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_temperature",
                "temperature": "hot",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_sets_fan_mode():
    class FanProvider(FakeHomeProvider):
        def __init__(self):
            super().__init__()
            self.fan_calls = []

        def set_fan_mode(
            self,
            entity_id,
            fan_mode,
        ):
            self.fan_calls.append(
                {
                    "entity_id": entity_id,
                    "fan_mode": fan_mode,
                }
            )

            return {
                "ok": True,
            }

    provider = FanProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_fan_mode",
                "fan_mode": "medium",
            }
        ).encode("utf-8"),
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload == {
        "ok": True,
    }

    assert provider.fan_calls == [
        {
            "entity_id": "climate.living_room",
            "fan_mode": "medium",
        }
    ]


def test_home_action_api_requires_fan_mode():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_fan_mode",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_rejects_non_string_fan_mode():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_fan_mode",
                "fan_mode": 3,
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_sets_hvac_mode():
    class HvacProvider(FakeHomeProvider):
        def __init__(self):
            super().__init__()
            self.hvac_calls = []

        def set_hvac_mode(
            self,
            entity_id,
            hvac_mode,
        ):
            self.hvac_calls.append(
                {
                    "entity_id": entity_id,
                    "hvac_mode": hvac_mode,
                }
            )

            return {
                "ok": True,
            }

    provider = HvacProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_hvac_mode",
                "hvac_mode": "heat",
            }
        ).encode("utf-8"),
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload == {
        "ok": True,
    }

    assert provider.hvac_calls == [
        {
            "entity_id": "climate.living_room",
            "hvac_mode": "heat",
        }
    ]


def test_home_action_api_requires_hvac_mode():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_hvac_mode",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_rejects_non_string_hvac_mode():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "climate.living_room",
                "action": "set_hvac_mode",
                "hvac_mode": 1,
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_performs_cover_action():
    class CoverProvider(FakeHomeProvider):
        def __init__(self):
            super().__init__()
            self.cover_calls = []

        def perform_cover_action(
            self,
            entity_id,
            cover_action,
        ):
            self.cover_calls.append(
                {
                    "entity_id": entity_id,
                    "cover_action": cover_action,
                }
            )

            return {
                "ok": True,
            }

    provider = CoverProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "cover.living_room",
                "action": "cover_action",
                "cover_action": "open",
            }
        ).encode("utf-8"),
    )

    payload = json.loads(
        body.decode("utf-8")
    )

    assert status == 200
    assert payload == {
        "ok": True,
    }

    assert provider.cover_calls == [
        {
            "entity_id": "cover.living_room",
            "cover_action": "open",
        }
    ]


def test_home_action_api_requires_cover_action():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "cover.living_room",
                "action": "cover_action",
            }
        ).encode("utf-8"),
    )

    assert status == 400


def test_home_action_api_rejects_non_string_cover_action():
    provider = FakeHomeProvider()
    app = create_app(provider)

    status, headers, body = app.handle(
        method="POST",
        path="/api/home/actions",
        body=json.dumps(
            {
                "entity_id": "cover.living_room",
                "action": "cover_action",
                "cover_action": 1,
            }
        ).encode("utf-8"),
    )

    assert status == 400

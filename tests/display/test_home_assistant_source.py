from src.smartscreen_display.home_assistant_source import (
    create_home_assistant_provider,
)


def test_source_returns_none_without_credentials(
    monkeypatch,
):
    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    provider = create_home_assistant_provider()

    assert provider is None


def test_source_uses_environment_credentials(
    monkeypatch,
):
    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    provider = create_home_assistant_provider()

    assert provider is not None
    assert (
        provider._client._base_url
        == "http://localhost:8123"
    )
    assert provider._client._token == "secret-token"


def test_source_uses_entity_config_file(
    monkeypatch,
    tmp_path,
):
    import json

    config_file = tmp_path / "entities.json"

    config_file.write_text(
        json.dumps(
            {
                "entities": [
                    {
                        "entity_id": "light.test",
                        "name": "测试灯",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    provider = create_home_assistant_provider(
        entities_file=config_file,
    )

    assert provider is not None
    assert provider._entities == [
        {
            "entity_id": "light.test",
            "name": "测试灯",
        }
    ]


def test_source_falls_back_when_entity_config_missing(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv(
        "SMARTSCREEN_HA_URL",
        "http://localhost:8123",
    )
    monkeypatch.setenv(
        "SMARTSCREEN_HA_TOKEN",
        "secret-token",
    )

    provider = create_home_assistant_provider(
        entities_file=tmp_path / "missing.json",
    )

    assert provider is not None
    assert len(provider._entities) > 0


def test_create_home_assistant_provider_accepts_existing_client():
    from src.smartscreen_display.home_assistant_source import (
        create_home_assistant_provider,
    )

    class FakeClient:
        pass

    client = FakeClient()

    provider = create_home_assistant_provider(
        client=client,
        entities=[],
    )

    assert provider is not None
    assert provider._client is client


def test_create_home_assistant_provider_with_client_does_not_require_environment(
    monkeypatch,
):
    from src.smartscreen_display.home_assistant_source import (
        create_home_assistant_provider,
    )

    monkeypatch.delenv(
        "SMARTSCREEN_HA_URL",
        raising=False,
    )
    monkeypatch.delenv(
        "SMARTSCREEN_HA_TOKEN",
        raising=False,
    )

    class FakeClient:
        pass

    client = FakeClient()

    provider = create_home_assistant_provider(
        client=client,
        entities=[],
    )

    assert provider is not None
    assert provider._client is client

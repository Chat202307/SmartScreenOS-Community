from scripts.check_qweather import (
    DEFAULT_LANGUAGE,
    DEFAULT_LOCATION,
    build_configuration,
)


def test_default_location_is_dalian():
    assert DEFAULT_LOCATION == "101010100"


def test_default_language_is_chinese(monkeypatch):
    monkeypatch.delenv(
        "SMARTSCREEN_QWEATHER_LANGUAGE",
        raising=False,
    )

    assert build_configuration() == {
        "provider": "qweather",
        "language": DEFAULT_LANGUAGE,
    }


def test_language_can_be_overridden(monkeypatch):
    monkeypatch.setenv(
        "SMARTSCREEN_QWEATHER_LANGUAGE",
        "en",
    )

    assert build_configuration() == {
        "provider": "qweather",
        "language": "en",
    }

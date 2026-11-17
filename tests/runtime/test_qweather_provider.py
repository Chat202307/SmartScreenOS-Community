import json
from datetime import datetime

import pytest

from examples.capabilities.weather.qweather_provider import (
    QWeatherApiError,
    QWeatherConfigurationError,
    QWeatherProvider,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeUrlOpener:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeResponse(self.payload)


def successful_payload() -> dict:
    return {
        "code": "200",
        "now": {
            "obsTime": "2026-08-07T08:00+08:00",
            "temp": "26",
            "text": "晴",
            "windSpeed": "12",
            "humidity": "58",
        },
    }


def test_fetch_maps_qweather_response():
    opener = FakeUrlOpener(successful_payload())

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        opener=opener,
    )

    result = provider.fetch("101010100")

    assert result["condition"] == "晴"
    assert result["temperature"] == 26.0
    assert result["humidity"] == 58
    assert result["windSpeed"] == 12.0
    assert result["observedAt"] == datetime.fromisoformat(
        "2026-08-07T08:00+08:00"
    )


def test_fetch_sends_api_key_in_header():
    opener = FakeUrlOpener(successful_payload())

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        opener=opener,
    )

    provider.fetch("101010100")

    assert opener.request.get_header("X-qw-api-key") == "test-api-key"
    assert "key=" not in opener.request.full_url.lower()


def test_fetch_builds_expected_url():
    opener = FakeUrlOpener(successful_payload())

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        language="zh",
        opener=opener,
    )

    provider.fetch("101010100")

    assert opener.request.full_url == (
        "https://abc1234xyz.def.qweatherapi.com"
        "/v7/weather/now"
        "?location=101010100&lang=zh"
    )


def test_invalid_api_code_is_rejected():
    opener = FakeUrlOpener(
        {
            "code": "401",
            "now": {},
        }
    )

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        opener=opener,
    )

    with pytest.raises(QWeatherApiError, match="401"):
        provider.fetch("101010100")


def test_missing_api_host_is_rejected():
    with pytest.raises(QWeatherConfigurationError, match="host"):
        QWeatherProvider(
            api_host="",
            api_key="test-api-key",
        )


def test_missing_api_key_is_rejected():
    with pytest.raises(QWeatherConfigurationError, match="key"):
        QWeatherProvider(
            api_host="abc1234xyz.def.qweatherapi.com",
            api_key="",
        )


def test_api_host_rejects_scheme():
    with pytest.raises(QWeatherConfigurationError, match="host"):
        QWeatherProvider(
            api_host="https://abc1234xyz.def.qweatherapi.com",
            api_key="test-api-key",
        )


def test_fetch_decodes_gzip_response():
    import gzip

    payload = gzip.compress(
        json.dumps(
            successful_payload()
        ).encode("utf-8")
    )

    class GzipResponse:
        def read(self) -> bytes:
            return payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    class GzipUrlOpener:
        def open(self, request, timeout):
            return GzipResponse()

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        opener=GzipUrlOpener(),
    )

    result = provider.fetch("101010100")

    assert result["condition"] == "晴"
    assert result["temperature"] == 26.0


def test_fetch_decodes_gzip_response():
    import gzip

    payload = gzip.compress(
        json.dumps(
            successful_payload()
        ).encode("utf-8")
    )

    class GzipResponse:
        def read(self) -> bytes:
            return payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    class GzipUrlOpener:
        def open(self, request, timeout):
            return GzipResponse()

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        opener=GzipUrlOpener(),
    )

    result = provider.fetch("101010100")

    assert result["condition"] == "晴"
    assert result["temperature"] == 26.0


def test_http_error_response_is_closed():
    from urllib.error import HTTPError

    class TrackingHttpError(HTTPError):
        def __init__(self):
            super().__init__(
                url="https://example.test/v7/weather/now",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None,
            )
            self.close_called = False

        def close(self):
            self.close_called = True
            super().close()

    error = TrackingHttpError()

    class FailingUrlOpener:
        def open(self, request, timeout):
            raise error

    provider = QWeatherProvider(
        api_host="abc1234xyz.def.qweatherapi.com",
        api_key="test-api-key",
        opener=FailingUrlOpener(),
    )

    with pytest.raises(QWeatherApiError, match="401"):
        provider.fetch("101010100")

    assert error.close_called is True

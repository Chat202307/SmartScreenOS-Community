from __future__ import annotations

import gzip
import json
from datetime import datetime
from typing import Any, Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class UrlOpener(Protocol):
    def open(self, request: Request, timeout: float):
        """Open an HTTP request."""


class DefaultUrlOpener:
    """Adapter around urllib.request.urlopen."""

    def open(self, request: Request, timeout: float):
        return urlopen(request, timeout=timeout)


class QWeatherError(Exception):
    """Base exception for QWeather provider errors."""


class QWeatherConfigurationError(QWeatherError):
    """Raised when the provider configuration is invalid."""


class QWeatherApiError(QWeatherError):
    """Raised when QWeather returns an unsuccessful response."""


class QWeatherResponseError(QWeatherError):
    """Raised when the QWeather response is malformed."""


class QWeatherProvider:
    """Fetch current weather observations from QWeather."""

    def __init__(
        self,
        api_host: str,
        api_key: str,
        language: str = "zh",
        timeout: float = 10.0,
        opener: UrlOpener | None = None,
    ) -> None:
        self._api_host = self._validate_api_host(api_host)
        self._api_key = self._validate_api_key(api_key)
        self._language = self._validate_language(language)
        self._timeout = self._validate_timeout(timeout)
        self._opener = opener or DefaultUrlOpener()

    def fetch(self, location: str) -> dict[str, Any]:
        location = self._validate_location(location)

        query = urlencode(
            {
                "location": location,
                "lang": self._language,
            }
        )
        url = (
            f"https://{self._api_host}"
            f"/v7/weather/now"
            f"?{query}"
        )

        request = Request(
            url,
            headers={
                "X-QW-Api-Key": self._api_key,
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with self._opener.open(
                request,
                timeout=self._timeout,
            ) as response:
                raw_payload = response.read()
        except HTTPError as exc:
            try:
                raise QWeatherApiError(
                    f"Unable to request QWeather data: {exc}"
                ) from exc
            finally:
                exc.close()
        except Exception as exc:
            raise QWeatherApiError(
                f"Unable to request QWeather data: {exc}"
            ) from exc

        payload = self._decode_payload(raw_payload)
        return self._map_payload(payload)

    @staticmethod
    def _validate_api_host(api_host: str) -> str:
        if not isinstance(api_host, str) or not api_host.strip():
            raise QWeatherConfigurationError(
                "QWeather API host must be a non-empty string."
            )

        normalized = api_host.strip()

        if "://" in normalized or "/" in normalized:
            raise QWeatherConfigurationError(
                "QWeather API host must contain only the host name."
            )

        return normalized

    @staticmethod
    def _validate_api_key(api_key: str) -> str:
        if not isinstance(api_key, str) or not api_key.strip():
            raise QWeatherConfigurationError(
                "QWeather API key must be a non-empty string."
            )

        return api_key.strip()

    @staticmethod
    def _validate_language(language: str) -> str:
        if not isinstance(language, str) or not language.strip():
            raise QWeatherConfigurationError(
                "QWeather language must be a non-empty string."
            )

        return language.strip()

    @staticmethod
    def _validate_timeout(timeout: float) -> float:
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise QWeatherConfigurationError(
                "QWeather timeout must be greater than zero."
            )

        return float(timeout)

    @staticmethod
    def _validate_location(location: str) -> str:
        if not isinstance(location, str) or not location.strip():
            raise QWeatherConfigurationError(
                "QWeather location must be a non-empty string."
            )

        return location.strip()

    @staticmethod
    def _decode_payload(raw_payload: bytes) -> dict[str, Any]:
        try:
            if raw_payload.startswith(b"\x1f\x8b"):
                raw_payload = gzip.decompress(raw_payload)

            payload = json.loads(raw_payload.decode("utf-8"))
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise QWeatherResponseError(
                "QWeather returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise QWeatherResponseError(
                "QWeather response must be a JSON object."
            )

        return payload

    @staticmethod
    def _map_payload(payload: dict[str, Any]) -> dict[str, Any]:
        code = str(payload.get("code", ""))

        if code != "200":
            raise QWeatherApiError(
                f"QWeather API returned code: {code or 'unknown'}"
            )

        now = payload.get("now")
        if not isinstance(now, dict):
            raise QWeatherResponseError(
                "QWeather response is missing the now object."
            )

        try:
            observed_at = datetime.fromisoformat(
                str(now["obsTime"])
            )

            return {
                "condition": str(now["text"]),
                "temperature": float(now["temp"]),
                "humidity": int(now["humidity"]),
                "windSpeed": float(now["windSpeed"]),
                "observedAt": observed_at,
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise QWeatherResponseError(
                "QWeather current-weather data is incomplete or invalid."
            ) from exc

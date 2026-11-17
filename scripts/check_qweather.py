from __future__ import annotations

import json
import os
import sys
from typing import Any

from examples.capabilities.weather.provider_factory import (
    WeatherProviderConfigurationError,
    create_weather_provider,
)
from examples.capabilities.weather.qweather_provider import QWeatherError


DEFAULT_LOCATION = "101010100"  # 示例城市
DEFAULT_LANGUAGE = "zh"


def build_configuration() -> dict[str, Any]:
    return {
        "provider": "qweather",
        "language": os.environ.get(
            "SMARTSCREEN_QWEATHER_LANGUAGE",
            DEFAULT_LANGUAGE,
        ),
    }


def main() -> int:
    location = os.environ.get(
        "SMARTSCREEN_WEATHER_LOCATION",
        DEFAULT_LOCATION,
    ).strip()

    if not location:
        print(
            "错误：SMARTSCREEN_WEATHER_LOCATION 不能为空。",
            file=sys.stderr,
        )
        return 2

    try:
        provider = create_weather_provider(
            build_configuration()
        )

        if provider is None:
            print(
                "错误：未能创建 QWeather Provider。",
                file=sys.stderr,
            )
            return 2

        result = provider.fetch(location)

    except WeatherProviderConfigurationError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        print(
            "\n请先设置：\n"
            '  export SMARTSCREEN_QWEATHER_API_HOST="你的专属Host"\n'
            '  export SMARTSCREEN_QWEATHER_API_KEY="你的API Key"',
            file=sys.stderr,
        )
        return 2

    except QWeatherError as exc:
        print(f"QWeather 请求失败：{exc}", file=sys.stderr)
        return 3

    except Exception as exc:
        print(
            f"未预期的错误：{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 4

    print("QWeather 实时天气请求成功：")
    print(
        json.dumps(
            {
                "location": location,
                "condition": result["condition"],
                "temperature": result["temperature"],
                "humidity": result["humidity"],
                "windSpeed": result["windSpeed"],
                "observedAt": result["observedAt"].isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

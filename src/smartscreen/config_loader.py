"""Load and validate SmartScreen OS JSON configuration."""

import json
from pathlib import Path


class ConfigError(ValueError):
    pass


def load_json(path: Path):
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Configuration root must be an object: {path}")

    return data


def load_all(config_dir: Path):
    names = (
        "system",
        "home",
        "devices",
        "dashboard",
        "adapters",
        "home_dashboard",
    )

    loaded = {
        name: load_json(config_dir / f"{name}.json")
        for name in names
    }

    required = {
        "system": ("schema_version", "system"),
        "home": ("schema_version", "home", "rooms"),
        "devices": ("schema_version", "devices"),
        "dashboard": ("schema_version", "dashboard"),
        "adapters": ("schema_version", "adapters"),
        "home_dashboard": ("schema_version", "home_dashboard"),
    }

    for name, keys in required.items():
        missing = [key for key in keys if key not in loaded[name]]
        if missing:
            raise ConfigError(
                f"{name}.json missing: {', '.join(missing)}"
            )

    return loaded

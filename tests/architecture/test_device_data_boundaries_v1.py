import ast
from pathlib import Path


PROJECT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DEVICE_DATA = (
    PROJECT
    / "src"
    / "smartscreen_platform"
    / "device_data"
)


def test_device_data_does_not_import_vendor_or_transport_modules():
    forbidden = (
        "src.smartscreen.adapters",
        "smartscreen_display",
        "homeassistant",
        "paho.mqtt",
        "xiaomi",
        "aqara",
        "dnake",
    )

    violations = []

    for path in DEVICE_DATA.rglob(
        "*.py"
    ):
        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.Import,
            ):
                modules = [
                    alias.name
                    for alias
                    in node.names
                ]
            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                modules = [
                    node.module or ""
                ]
            else:
                modules = []

            for module in modules:
                if any(
                    item in module
                    for item in forbidden
                ):
                    violations.append(
                        (
                            str(path),
                            module,
                        )
                    )

    assert violations == []

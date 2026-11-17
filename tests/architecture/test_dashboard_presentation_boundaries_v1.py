import ast
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]

PLATFORM = (
    PROJECT
    / "src"
    / "smartscreen_platform"
)

PRESENTATION = (
    PROJECT
    / "src"
    / "smartscreen_display"
    / "presentation"
)


def imports_in(directory):
    imports = set()

    for path in directory.rglob("*.py"):
        tree = ast.parse(
            path.read_text(encoding="utf-8")
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(
                    alias.name
                    for alias in node.names
                )

            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")

    return imports


def test_platform_does_not_depend_on_display_presentation():
    imports = imports_in(PLATFORM)

    for imported in imports:
        assert "smartscreen_display" not in imported, (
            "Platform must not depend on display "
            "or presentation."
        )


def test_presentation_does_not_depend_on_http_or_dashboard_ui():
    imports = imports_in(PRESENTATION)

    for imported in imports:
        assert "http.server" not in imported
        assert "smartscreen_display.server" not in imported
        assert "smartscreen_display.dashboard" not in imported

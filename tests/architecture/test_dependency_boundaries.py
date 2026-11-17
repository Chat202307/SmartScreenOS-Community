import ast
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
SRC = PROJECT / "src" / "smartscreen"


class DependencyBoundaryTests(unittest.TestCase):
    def _imports_in(self, directory):
        imports = set()
        for path in directory.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.add(node.module or "")
        return imports

    def test_experience_does_not_import_mqtt_adapter(self):
        imports = self._imports_in(SRC / "experience")
        forbidden = {
            "src.smartscreen.adapters.mqtt",
            "smartscreen.adapters.mqtt",
        }
        self.assertTrue(
            imports.isdisjoint(forbidden),
            "Experience must consume HomeEvent, never MQTT directly.",
        )

    def test_policy_does_not_import_dashboard(self):
        imports = self._imports_in(SRC / "policy")
        for imported in imports:
            self.assertFalse(
                "dashboard" in imported or "http.server" in imported,
                "Policy must not depend on dashboard or HTTP presentation.",
            )

    def test_companion_does_not_import_device_adapters(self):
        imports = self._imports_in(SRC / "companion")
        for imported in imports:
            self.assertNotIn(
                ".adapters.",
                imported,
                "Companion must not depend on device adapters.",
            )


if __name__ == "__main__":
    unittest.main()

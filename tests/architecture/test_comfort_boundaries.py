import ast
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
COMFORT = (
    PROJECT
    / "src"
    / "smartscreen_platform"
    / "capabilities"
    / "comfort"
)


class ComfortBoundaryTests(unittest.TestCase):
    def test_comfort_does_not_import_runtime_or_device_adapters(self):
        violations = []

        for path in COMFORT.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                else:
                    modules = []

                for module in modules:
                    if (
                        "src.smartscreen.adapters" in module
                        or "paho.mqtt" in module
                        or "device_types" in module
                    ):
                        violations.append((str(path), module))

        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

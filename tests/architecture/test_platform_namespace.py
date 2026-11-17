import ast
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
PLATFORM = PROJECT / "src" / "smartscreen_platform"

class PlatformNamespaceTests(unittest.TestCase):
    def test_platform_does_not_import_runtime(self):
        violations = []
        for path in PLATFORM.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("src.smartscreen."):
                            violations.append((str(path), alias.name))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module.startswith("src.smartscreen."):
                        violations.append((str(path), module))
        self.assertEqual(violations, [])

    def test_runtime_modules_are_not_shadowed(self):
        for name in ("events", "policy"):
            self.assertTrue((PROJECT / ("src/smartscreen/" + name + ".py")).is_file())
            self.assertFalse((PROJECT / ("src/smartscreen/" + name)).is_dir())

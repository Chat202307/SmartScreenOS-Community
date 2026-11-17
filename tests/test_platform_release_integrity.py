import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class PlatformReleaseIntegrityTests(unittest.TestCase):
    def test_expected_platform_files_exist(self):
        expected = [
            "src/smartscreen_platform/contracts/observation.py",
            "src/smartscreen_platform/contracts/interpretation.py",
            "src/smartscreen_platform/contracts/state.py",
            "src/smartscreen_platform/interpretation/thermal.py",
            "src/smartscreen_platform/interpretation/presence.py",
            "src/smartscreen_platform/interpretation/illuminance.py",
            "src/smartscreen_platform/knowledge/static.py",
            "src/smartscreen_platform/state_pipeline.py",
        ]

        missing = [
            item for item in expected
            if not (PROJECT / item).is_file()
        ]

        self.assertEqual(
            missing,
            [],
            "Release files are missing: %r" % missing,
        )

    def test_nested_test_packages_exist(self):
        self.assertTrue((PROJECT / "tests/platform/__init__.py").is_file())
        self.assertTrue((PROJECT / "tests/architecture/__init__.py").is_file())


if __name__ == "__main__":
    unittest.main()

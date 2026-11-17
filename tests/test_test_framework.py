import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class TestFrameworkIntegrityTests(unittest.TestCase):
    def test_runner_exists(self):
        self.assertTrue((PROJECT / "tools/test_runner.py").is_file())

    def test_platform_tests_exist(self):
        files = list((PROJECT / "tests/platform").glob("test_*.py"))
        self.assertGreater(len(files), 0)

    def test_architecture_tests_exist(self):
        files = list((PROJECT / "tests/architecture").glob("test_*.py"))
        self.assertGreater(len(files), 0)


if __name__ == "__main__":
    unittest.main()

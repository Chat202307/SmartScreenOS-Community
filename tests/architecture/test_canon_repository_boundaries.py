import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
CANON = PROJECT / "canon"

class CanonRepositoryBoundaryTests(unittest.TestCase):
    def test_canon_is_top_level_asset(self):
        self.assertEqual(CANON.parent, PROJECT)
        self.assertTrue((PROJECT / "src").is_dir())
        self.assertTrue((PROJECT / "tests").is_dir())

    def test_canon_contains_no_python(self):
        self.assertEqual(list(CANON.rglob("*.py")), [])

    def test_foundation_core_objects_present(self):
        text = (
            CANON / "SC-1000_Foundation_Specification" / "SC-1000.md"
        ).read_text(encoding="utf-8")

        for term in (
            "Household",
            "Entity",
            "Observation",
            "State",
            "Event",
            "Context",
        ):
            self.assertIn(term, text)

if __name__ == "__main__":
    unittest.main()

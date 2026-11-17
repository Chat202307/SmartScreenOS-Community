import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
CANON = PROJECT / "canon"

class CanonFoundationTests(unittest.TestCase):
    def test_required_documents_exist(self):
        required = [
            "README.md",
            "INDEX.md",
            "SC-0000_Canon_Governance/SC-0000.md",
            "SC-0100_Glossary/SC-0100.md",
            "SC-1000_Foundation_Specification/SC-1000.md",
            "SC-3000_Architecture_Specification/SC-3000.md",
            "SC-4000_Engineering_Standards/SC-4000.md",
        ]
        self.assertEqual(
            [x for x in required if not (CANON / x).is_file()],
            [],
        )

    def test_index_lists_core_documents(self):
        index = (CANON / "INDEX.md").read_text(encoding="utf-8")
        for doc_id in ("SC-0000", "SC-0100", "SC-1000", "SC-3000", "SC-4000"):
            self.assertIn(doc_id, index)

    def test_documents_declare_version_and_status(self):
        docs = list(CANON.glob("SC-*/*.md"))
        self.assertGreaterEqual(len(docs), 5)
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertRegex(
                text,
                r"(?m)^\| Version \| [^|\n]+ \|$",
                msg=f"{path} must declare Version metadata",
            )
            self.assertRegex(
                text,
                r"(?m)^\| Status \| [^|\n]+ \|$",
                msg=f"{path} must declare Status metadata",
            )

if __name__ == "__main__":
    unittest.main()

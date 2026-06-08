import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs" / "feishu-collab" / "registry" / "skill-audit-matrix.json"
AUDIT_DIR = ROOT / "docs" / "feishu-collab" / "audits"


class FeishuCollabAuditRegistryTests(unittest.TestCase):
    def test_matrix_covers_all_five_core_skills(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        names = {item["skill"] for item in matrix["skills"]}
        self.assertEqual(
            names,
            {
                "OKR-driven",
                "Bitable",
                "GitHub-Feishu",
                "Approval",
                "Knowledge-Ops",
            },
        )

    def test_remaining_four_skills_have_audit_docs(self):
        expected = {
            "bitable-skill-audit.md",
            "github-sync-skill-audit.md",
            "approval-skill-audit.md",
            "knowledge-ops-skill-audit.md",
        }
        existing = {path.name for path in AUDIT_DIR.glob("*.md")}
        self.assertTrue(expected.issubset(existing))

    def test_each_matrix_entry_has_status_and_next_plan(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        for item in matrix["skills"]:
            self.assertIn("status", item)
            self.assertIn("next_plan", item)


if __name__ == "__main__":
    unittest.main()

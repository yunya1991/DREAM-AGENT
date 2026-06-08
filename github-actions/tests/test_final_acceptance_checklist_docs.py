import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FinalAcceptanceChecklistDocsTests(unittest.TestCase):
    def test_final_acceptance_checklist_mentions_all_three_workflows(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "final-acceptance-checklist.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/real-approval-trigger.yml", text)
        self.assertIn(".github/workflows/approval-polling-writeback.yml", text)
        self.assertIn(".github/workflows/knowledge-materialization.yml", text)
        self.assertIn("approval:instance:read", text)

    def test_runbook_index_registers_final_acceptance_checklist(self):
        text = (REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Final Acceptance Checklist", text)
        self.assertIn("final-acceptance-checklist.md", text)


if __name__ == "__main__":
    unittest.main()

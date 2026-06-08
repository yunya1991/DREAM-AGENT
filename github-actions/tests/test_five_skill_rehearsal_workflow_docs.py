import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FiveSkillRehearsalWorkflowDocsTests(unittest.TestCase):
    def test_runbook_mentions_workflow_entry_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "five-skill-integration-rehearsal.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/five-skill-rehearsal.yml", text)
        self.assertIn("workflow_dispatch", text)
        self.assertIn("five-skill-rehearsal-report.json", text)
        self.assertIn("Job Summary", text)


if __name__ == "__main__":
    unittest.main()

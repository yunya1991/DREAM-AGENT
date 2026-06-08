import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RealApprovalTriggerDocsTests(unittest.TestCase):
    def test_real_approval_runbook_mentions_workflow_inputs_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "real-approval-trigger.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/real-approval-trigger.yml", text)
        self.assertIn("approval_code", text)
        self.assertIn("applicant_open_id", text)
        self.assertIn("approval_dispatch_result.json", text)
        self.assertIn("approval_status_result.json", text)


if __name__ == "__main__":
    unittest.main()

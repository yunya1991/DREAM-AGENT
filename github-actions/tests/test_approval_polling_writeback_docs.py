import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ApprovalPollingWritebackDocsTests(unittest.TestCase):
    def test_polling_runbook_mentions_workflow_inputs_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "approval-polling-writeback.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/approval-polling-writeback.yml", text)
        self.assertIn("approval_instance_code", text)
        self.assertIn("base_sync_json", text)
        self.assertIn("approval_status_result.json", text)
        self.assertIn("approval_writeback_result.json", text)

    def test_runbook_index_registers_polling_writeback_entry(self):
        text = (REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Approval Polling Writeback", text)
        self.assertIn("approval-polling-writeback.md", text)

    def test_real_approval_trigger_runbook_points_to_polling_follow_up(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "real-approval-trigger.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/approval-polling-writeback.yml", text)


if __name__ == "__main__":
    unittest.main()

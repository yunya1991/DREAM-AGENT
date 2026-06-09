import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class AutomationRecoveryPolicyDocsTests(unittest.TestCase):
    def test_policy_documents_allowed_and_disabled_local_automation(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "automation-recovery-policy.md"
        ).read_text(encoding="utf-8")
        self.assertIn("read-only inspection", text)
        self.assertIn("Dispatch-only execution", text)
        self.assertIn("Permanently Disabled Local Automation", text)
        self.assertIn(".github/workflows/controlled-dispatch.yml", text)
        self.assertIn("Dream-Agent Hybrid Dispatch Executor", text)
        self.assertIn("dream-acceptance-hourly", text)

    def test_policy_is_registered_in_runbook_index(self):
        text = (REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Automation Recovery Policy", text)
        self.assertIn("automation-recovery-policy.md", text)


if __name__ == "__main__":
    unittest.main()

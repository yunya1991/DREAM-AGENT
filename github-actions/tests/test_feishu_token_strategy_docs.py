import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FeishuTokenStrategyDocsTests(unittest.TestCase):
    def test_token_strategy_runbook_documents_identity_selection_and_storage(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "feishu-token-strategy.md"
        ).read_text(encoding="utf-8")
        self.assertIn("tenant_access_token", text)
        self.assertIn("user_access_token", text)
        self.assertIn("LARK_APP_ID", text)
        self.assertIn("LARK_APP_SECRET", text)
        self.assertIn("GitHub Secrets", text)
        self.assertIn("lark-cli --as user", text)

    def test_token_strategy_runbook_is_registered_and_referenced_by_final_checklist(self):
        index_text = (REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
            encoding="utf-8"
        )
        checklist_text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "final-acceptance-checklist.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Feishu Token Strategy", index_text)
        self.assertIn("feishu-token-strategy.md", index_text)
        self.assertIn("tenant_access_token", checklist_text)
        self.assertIn("user_access_token", checklist_text)


if __name__ == "__main__":
    unittest.main()

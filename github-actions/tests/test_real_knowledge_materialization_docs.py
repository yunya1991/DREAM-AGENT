import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RealKnowledgeMaterializationDocsTests(unittest.TestCase):
    def test_runbook_mentions_workflow_inputs_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "knowledge-materialization.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/knowledge-materialization.yml", text)
        self.assertIn("approval_status_result_json", text)
        self.assertIn("approval_writeback_result_json", text)
        self.assertIn("knowledge_materialization_result.json", text)

    def test_runbook_index_registers_knowledge_materialization(self):
        text = (
            REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Knowledge Materialization", text)
        self.assertIn("knowledge-materialization.md", text)


if __name__ == "__main__":
    unittest.main()

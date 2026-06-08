import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "update_knowledge_indexes.py"
SPEC = importlib.util.spec_from_file_location("update_knowledge_indexes", MODULE_PATH)


class UpdateKnowledgeIndexesTests(unittest.TestCase):
    maxDiff = None

    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def write_indexes(self, repo_root, runbook_text, handoff_text):
        docs_root = repo_root / "docs" / "feishu-collab"
        docs_root.mkdir(parents=True, exist_ok=True)
        (docs_root / "RUNBOOK_INDEX.md").write_text(runbook_text, encoding="utf-8")
        (docs_root / "HANDOFF_INDEX.md").write_text(handoff_text, encoding="utf-8")

    def test_update_indexes_inserts_runbook_and_handoff_entries(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self.write_indexes(
                repo_root=repo_root,
                runbook_text=(
                    "# Runbook Index\n\n"
                    "## Entries\n\n"
                    "| Runbook | Path | Purpose |\n"
                    "| --- | --- | --- |\n"
                ),
                handoff_text=(
                    "# Handoff Index\n\n"
                    "## Categories\n\n"
                    "- Stage handoff\n"
                    "- Fault handoff\n\n"
                    "## Required Fields\n\n"
                    "- Background\n"
                ),
            )

            result = module.update_knowledge_indexes(
                repo_root=repo_root,
                runbook_entry={
                    "title": "Approval TASK-123 Runbook",
                    "path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    "purpose": "Track approval TASK-123 recovery and verification",
                },
                handoff_entry={
                    "title": "Approval TASK-123 Handoff",
                    "path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    "purpose": "Hand off approval TASK-123 next actions",
                },
            )

            runbook_text = (repo_root / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
                encoding="utf-8"
            )
            handoff_text = (repo_root / "docs" / "feishu-collab" / "HANDOFF_INDEX.md").read_text(
                encoding="utf-8"
            )

            self.assertEqual(result["runbook_index_status"], "success")
            self.assertEqual(result["handoff_index_status"], "success")
            self.assertIn("Approval TASK-123 Runbook", runbook_text)
            self.assertIn("Approval TASK-123 Handoff", handoff_text)
            self.assertIn("| Handoff | Path | Purpose |", handoff_text)

    def test_update_indexes_replaces_existing_entries_in_place(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self.write_indexes(
                repo_root=repo_root,
                runbook_text=(
                    "# Runbook Index\n\n"
                    "## Entries\n\n"
                    "| Runbook | Path | Purpose |\n"
                    "| --- | --- | --- |\n"
                    "| Approval TASK-123 Runbook | `docs/feishu-collab/runbooks/approval-task-123-runbook.md` | Existing purpose |\n"
                ),
                handoff_text=(
                    "# Handoff Index\n\n"
                    "## Entries\n\n"
                    "| Handoff | Path | Purpose |\n"
                    "| --- | --- | --- |\n"
                    "| Approval TASK-123 Handoff | `docs/feishu-collab/handoffs/approval-task-123-handoff.md` | Existing purpose |\n"
                ),
            )

            module.update_knowledge_indexes(
                repo_root=repo_root,
                runbook_entry={
                    "title": "Approval TASK-123 Runbook",
                    "path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    "purpose": "Updated purpose",
                },
                handoff_entry={
                    "title": "Approval TASK-123 Handoff",
                    "path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    "purpose": "Updated purpose",
                },
            )

            runbook_text = (repo_root / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
                encoding="utf-8"
            )
            handoff_text = (repo_root / "docs" / "feishu-collab" / "HANDOFF_INDEX.md").read_text(
                encoding="utf-8"
            )

            self.assertEqual(runbook_text.count("Approval TASK-123 Runbook"), 1)
            self.assertEqual(handoff_text.count("Approval TASK-123 Handoff"), 1)
            self.assertIn("Updated purpose", runbook_text)
            self.assertIn("Updated purpose", handoff_text)
            self.assertNotIn("Existing purpose", runbook_text)
            self.assertNotIn("Existing purpose", handoff_text)

    def test_update_indexes_deduplicates_multiple_existing_rows(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self.write_indexes(
                repo_root=repo_root,
                runbook_text=(
                    "# Runbook Index\n\n"
                    "## Entries\n\n"
                    "| Runbook | Path | Purpose |\n"
                    "| --- | --- | --- |\n"
                    "| Approval TASK-123 Runbook | `docs/feishu-collab/runbooks/approval-task-123-runbook.md` | Stale A |\n"
                    "| Approval TASK-123 Runbook | `docs/feishu-collab/runbooks/approval-task-123-runbook.md` | Stale B |\n"
                ),
                handoff_text=(
                    "# Handoff Index\n\n"
                    "## Entries\n\n"
                    "| Handoff | Path | Purpose |\n"
                    "| --- | --- | --- |\n"
                    "| Approval TASK-123 Handoff | `docs/feishu-collab/handoffs/approval-task-123-handoff.md` | Stale A |\n"
                    "| Approval TASK-123 Handoff | `docs/feishu-collab/handoffs/approval-task-123-handoff.md` | Stale B |\n"
                ),
            )

            module.update_knowledge_indexes(
                repo_root=repo_root,
                runbook_entry={
                    "title": "Approval TASK-123 Runbook",
                    "path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    "purpose": "Canonical purpose",
                },
                handoff_entry={
                    "title": "Approval TASK-123 Handoff",
                    "path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    "purpose": "Canonical purpose",
                },
            )

            runbook_text = (repo_root / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(
                encoding="utf-8"
            )
            handoff_text = (repo_root / "docs" / "feishu-collab" / "HANDOFF_INDEX.md").read_text(
                encoding="utf-8"
            )

            self.assertEqual(runbook_text.count("Approval TASK-123 Runbook"), 1)
            self.assertEqual(handoff_text.count("Approval TASK-123 Handoff"), 1)
            self.assertIn("Canonical purpose", runbook_text)
            self.assertIn("Canonical purpose", handoff_text)
            self.assertNotIn("Stale A", runbook_text)
            self.assertNotIn("Stale B", runbook_text)
            self.assertNotIn("Stale A", handoff_text)
            self.assertNotIn("Stale B", handoff_text)


if __name__ == "__main__":
    unittest.main()

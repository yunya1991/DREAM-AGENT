import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_real_knowledge_assets.py"
SPEC = importlib.util.spec_from_file_location("materialize_real_knowledge_assets", MODULE_PATH)


class MaterializeRealKnowledgeAssetsTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_payload(self):
        return {
            "source_refs": {
                "approval_instance_code": "ins_123",
                "task_id": "TASK-123",
                "goal_id": "GOAL-123",
            },
            "runbook": {
                "title": "Approval TASK-123 Runbook",
                "target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
            },
            "handoff": {
                "title": "Approval TASK-123 Handoff",
                "target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
            },
        }

    def sample_status_result(self, approval_status="pending", automation_status="paused"):
        return {
            "approval_instance_code": "ins_123",
            "approval_status": approval_status,
            "automation_status": automation_status,
            "decision_summary": f"{approval_status}:TASK-123",
        }

    def sample_writeback_result(self, task_writeback_status="success", goal_writeback_status="success"):
        return {
            "task_id": "TASK-123",
            "goal_id": "GOAL-123",
            "task_writeback_status": task_writeback_status,
            "goal_writeback_status": goal_writeback_status,
        }

    def test_materialize_assets_writes_both_documents(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            result = module.materialize_real_knowledge_assets(
                repo_root=repo_root,
                payload=self.sample_payload(),
                approval_status_result=self.sample_status_result(),
                approval_writeback_result=self.sample_writeback_result(),
            )

            runbook_path = repo_root / "docs/feishu-collab/runbooks/approval-task-123-runbook.md"
            handoff_path = repo_root / "docs/feishu-collab/handoffs/approval-task-123-handoff.md"

            self.assertEqual(result["runbook"]["write_status"], "success")
            self.assertEqual(result["handoff"]["write_status"], "success")
            self.assertTrue(runbook_path.exists())
            self.assertTrue(handoff_path.exists())
            self.assertIn("Approval TASK-123 Runbook", runbook_path.read_text(encoding="utf-8"))
            self.assertIn("Approval TASK-123 Handoff", handoff_path.read_text(encoding="utf-8"))

    def test_materialize_assets_stably_overwrites_same_task_outputs(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            first_result = module.materialize_real_knowledge_assets(
                repo_root=repo_root,
                payload=self.sample_payload(),
                approval_status_result=self.sample_status_result(approval_status="pending"),
                approval_writeback_result=self.sample_writeback_result(),
            )
            second_result = module.materialize_real_knowledge_assets(
                repo_root=repo_root,
                payload=self.sample_payload(),
                approval_status_result=self.sample_status_result(approval_status="approved", automation_status="resumed"),
                approval_writeback_result=self.sample_writeback_result(
                    task_writeback_status="updated",
                    goal_writeback_status="updated",
                ),
            )

            runbook_path = repo_root / "docs/feishu-collab/runbooks/approval-task-123-runbook.md"
            handoff_path = repo_root / "docs/feishu-collab/handoffs/approval-task-123-handoff.md"
            runbook_text = runbook_path.read_text(encoding="utf-8")
            handoff_text = handoff_path.read_text(encoding="utf-8")

            self.assertEqual(first_result["runbook"]["target_path"], second_result["runbook"]["target_path"])
            self.assertEqual(first_result["handoff"]["target_path"], second_result["handoff"]["target_path"])
            self.assertIn("Approval Status: `approved`", runbook_text)
            self.assertNotIn("Approval Status: `pending`", runbook_text)
            self.assertIn("Automation Status: `resumed`", handoff_text)
            self.assertIn("Task Writeback: `updated`", handoff_text)

    def test_handoff_failure_keeps_runbook_file_and_failure_evidence(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            handoff_path = repo_root / "docs/feishu-collab/handoffs/approval-task-123-handoff.md"
            handoff_path.parent.mkdir(parents=True, exist_ok=True)
            handoff_path.mkdir()

            result = module.materialize_real_knowledge_assets(
                repo_root=repo_root,
                payload=self.sample_payload(),
                approval_status_result=self.sample_status_result(),
                approval_writeback_result=self.sample_writeback_result(),
            )

            runbook_path = repo_root / "docs/feishu-collab/runbooks/approval-task-123-runbook.md"
            self.assertEqual(result["runbook"]["write_status"], "success")
            self.assertEqual(result["handoff"]["write_status"], "failed")
            self.assertTrue(runbook_path.exists())
            self.assertIn("Approval TASK-123 Runbook", runbook_path.read_text(encoding="utf-8"))
            self.assertIn("docs/feishu-collab/runbooks/approval-task-123-runbook.md", result["runbook"]["evidence_refs"])
            self.assertEqual(result["handoff"]["target_path"], "docs/feishu-collab/handoffs/approval-task-123-handoff.md")
            self.assertIn("error", result["handoff"])


if __name__ == "__main__":
    unittest.main()

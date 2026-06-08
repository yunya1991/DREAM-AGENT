import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_real_knowledge_materialization.py"
SPEC = importlib.util.spec_from_file_location(
    "run_real_knowledge_materialization",
    MODULE_PATH,
)


class RunRealKnowledgeMaterializationTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_run_materialization_returns_combined_success_result(self):
        module = self.load_module()

        with patch.object(module.BUILDER, "build_real_knowledge_payload") as mock_build, patch.object(
            module.MATERIALIZE,
            "materialize_real_knowledge_assets",
        ) as mock_materialize, patch.object(
            module.UPDATE,
            "update_knowledge_indexes",
        ) as mock_update:
            mock_build.return_value = {
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
            mock_materialize.return_value = {
                "runbook": {
                    "target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    "write_status": "success",
                    "index_status": "pending",
                    "evidence_refs": ["docs/feishu-collab/runbooks/approval-task-123-runbook.md"],
                },
                "handoff": {
                    "target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    "write_status": "success",
                    "index_status": "pending",
                    "evidence_refs": ["docs/feishu-collab/handoffs/approval-task-123-handoff.md"],
                },
            }
            mock_update.return_value = {
                "runbook_index_status": "success",
                "handoff_index_status": "success",
            }

            result = module.run_materialization(
                repo_root=ROOT,
                payload={
                    "approval_status_result": {"approval_instance_code": "ins_123"},
                    "approval_writeback_result": {"task_id": "TASK-123", "goal_id": "GOAL-123"},
                    "materialization_context": {"workflow_name": "approval-polling-writeback"},
                },
            )

        self.assertEqual(result["materialization_status"], "success")
        self.assertEqual(result["index_update_status"], "success")
        self.assertEqual(
            result["runbook"]["target_path"],
            "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
        )
        self.assertEqual(
            result["handoff"]["target_path"],
            "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
        )
        self.assertEqual(len(result["evidence_refs"]), 2)

    def test_run_materialization_preserves_partial_failure_and_skips_index_update(self):
        module = self.load_module()

        with patch.object(module.BUILDER, "build_real_knowledge_payload") as mock_build, patch.object(
            module.MATERIALIZE,
            "materialize_real_knowledge_assets",
        ) as mock_materialize, patch.object(
            module.UPDATE,
            "update_knowledge_indexes",
        ) as mock_update:
            mock_build.return_value = {
                "source_refs": {
                    "approval_instance_code": "ins_456",
                    "task_id": "TASK-456",
                    "goal_id": "GOAL-456",
                },
                "runbook": {
                    "title": "Approval TASK-456 Runbook",
                    "target_path": "docs/feishu-collab/runbooks/approval-task-456-runbook.md",
                },
                "handoff": {
                    "title": "Approval TASK-456 Handoff",
                    "target_path": "docs/feishu-collab/handoffs/approval-task-456-handoff.md",
                },
            }
            mock_materialize.return_value = {
                "runbook": {
                    "target_path": "docs/feishu-collab/runbooks/approval-task-456-runbook.md",
                    "write_status": "success",
                    "index_status": "pending",
                    "evidence_refs": ["docs/feishu-collab/runbooks/approval-task-456-runbook.md"],
                },
                "handoff": {
                    "target_path": "docs/feishu-collab/handoffs/approval-task-456-handoff.md",
                    "write_status": "failed",
                    "index_status": "pending",
                    "evidence_refs": [],
                    "error": "handoff write failed",
                },
            }

            result = module.run_materialization(
                repo_root=ROOT,
                payload={
                    "approval_status_result": {"approval_instance_code": "ins_456"},
                    "approval_writeback_result": {"task_id": "TASK-456", "goal_id": "GOAL-456"},
                    "materialization_context": {"workflow_name": "approval-polling-writeback"},
                },
            )

        self.assertEqual(result["materialization_status"], "failed")
        self.assertEqual(result["index_update_status"], "skipped")
        self.assertEqual(result["failure_reason"], "materialization_incomplete")
        self.assertEqual(result["runbook"]["write_status"], "success")
        self.assertEqual(result["handoff"]["write_status"], "failed")
        mock_update.assert_not_called()


if __name__ == "__main__":
    unittest.main()

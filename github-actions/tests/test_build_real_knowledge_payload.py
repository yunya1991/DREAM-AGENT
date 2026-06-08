import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT
    / "github-actions"
    / "feishu_collab"
    / "knowledge_ops"
    / "build_real_knowledge_payload.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_real_knowledge_payload",
    MODULE_PATH,
)


class BuildRealKnowledgePayloadTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_payload_creates_stable_runbook_and_handoff_specs(self):
        module = self.load_module()
        payload = module.build_real_knowledge_payload(
            approval_status_result={
                "approval_instance_code": "ins_123",
                "approval_status": "pending",
                "automation_status": "paused",
                "decision_summary": "pending:TASK-123",
            },
            approval_writeback_result={
                "task_id": "TASK-123",
                "goal_id": "GOAL-123",
                "task_writeback_status": "success",
                "goal_writeback_status": "success",
            },
            materialization_context={
                "workflow_name": "approval-polling-writeback",
                "operator_summary": "Approval waiting for review",
            },
        )

        self.assertEqual(
            payload["runbook"]["target_path"],
            "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
        )
        self.assertEqual(
            payload["handoff"]["target_path"],
            "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
        )
        self.assertEqual(payload["runbook"]["title"], "Approval TASK-123 Runbook")
        self.assertEqual(payload["handoff"]["title"], "Approval TASK-123 Handoff")
        self.assertEqual(payload["source_refs"]["approval_instance_code"], "ins_123")
        self.assertEqual(payload["source_refs"]["task_id"], "TASK-123")
        self.assertEqual(payload["source_refs"]["goal_id"], "GOAL-123")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_real_approval_summary.py"
SPEC = importlib.util.spec_from_file_location("render_real_approval_summary", MODULE_PATH)


class RenderRealApprovalSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_dispatch(self):
        return {
            "approval_code": "approval-code",
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "approval_instance_code": "ins_123",
            "approval_status": "pending",
            "automation_status": "paused",
            "decision_summary": "approval_created",
        }

    def sample_query(self, status="pending"):
        return {
            "approval_instance_code": "ins_123",
            "approval_status": status,
            "automation_status": "paused" if status == "pending" else "running",
            "decision_summary": "pending:TASK-1" if status == "pending" else "approved:TASK-1",
        }

    def test_build_summary_markdown_renders_core_approval_fields(self):
        module = self.load_module()
        summary = module.build_summary_markdown(self.sample_dispatch(), self.sample_query())
        self.assertIn("approval-code", summary)
        self.assertIn("ins_123", summary)
        self.assertIn("TASK-1", summary)
        self.assertIn("pending", summary)

    def test_workflow_exit_code_is_zero_only_when_instance_and_status_exist(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_dispatch(), self.sample_query("approved")), 0)
        self.assertEqual(module.workflow_exit_code(self.sample_dispatch(), {}), 1)
        self.assertEqual(module.workflow_exit_code({"approval_instance_code": ""}, self.sample_query()), 1)


if __name__ == "__main__":
    unittest.main()

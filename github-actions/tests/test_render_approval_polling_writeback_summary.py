import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_approval_polling_writeback_summary.py"
SPEC = importlib.util.spec_from_file_location(
    "render_approval_polling_writeback_summary",
    MODULE_PATH,
)


class RenderApprovalPollingWritebackSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_status(self):
        return {
            "approval_instance_code": "ins_123",
            "approval_status": "approved",
            "automation_status": "proceed",
            "decision_summary": "approved:TASK-1",
        }

    def sample_writeback(self, task_status="success", goal_status="success"):
        return {
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "task_writeback_status": task_status,
            "goal_writeback_status": goal_status,
            "writeback_receipts": {
                "task": {"record_id": "rec_task"},
                "goal": {"record_id": "rec_goal"},
            },
        }

    def test_build_summary_markdown_renders_core_statuses(self):
        module = self.load_module()
        summary = module.build_summary_markdown(self.sample_status(), self.sample_writeback())
        self.assertIn("ins_123", summary)
        self.assertIn("approved", summary)
        self.assertIn("proceed", summary)
        self.assertIn("TASK-1", summary)
        self.assertIn("success", summary)

    def test_workflow_exit_code_requires_query_and_both_writebacks(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_status(), self.sample_writeback()), 0)
        self.assertEqual(module.workflow_exit_code({}, self.sample_writeback()), 1)
        self.assertEqual(
            module.workflow_exit_code(
                self.sample_status(),
                self.sample_writeback(goal_status="failed"),
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()

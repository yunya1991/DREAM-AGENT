import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_approval_polling_writeback.py"
SPEC = importlib.util.spec_from_file_location("run_approval_polling_writeback", MODULE_PATH)


class RunApprovalPollingWritebackTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_payload(self):
        return {
            "task_payload": {"task_id": "TASK-1"},
            "goal_payload": {"goal_id": "GOAL-1"},
            "status_result": {
                "approval_instance_code": "ins_123",
                "approval_status": "approved",
                "automation_status": "running",
                "decision_summary": "approved:TASK-1",
            },
        }

    def test_build_writeback_result_contains_statuses_and_receipts(self):
        module = self.load_module()
        with patch.object(module.POLL, "sync_with_status_result") as mock_sync:
            mock_sync.return_value = {
                "task_record": {"任务ID": "TASK-1"},
                "goal_record": {"goal_id": "GOAL-1"},
                "task_writeback_status": "success",
                "goal_writeback_status": "success",
                "task_writeback_receipt": {"record_id": "rec_task"},
                "goal_writeback_receipt": {"record_id": "rec_goal"},
            }
            result = module.run_writeback(self.sample_payload())
        self.assertEqual(result["task_id"], "TASK-1")
        self.assertEqual(result["goal_id"], "GOAL-1")
        self.assertEqual(result["task_writeback_status"], "success")
        self.assertEqual(result["goal_writeback_status"], "success")
        self.assertEqual(result["writeback_receipts"]["task"]["record_id"], "rec_task")


if __name__ == "__main__":
    unittest.main()

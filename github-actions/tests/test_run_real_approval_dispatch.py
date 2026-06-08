import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_real_approval_dispatch.py"
SPEC = importlib.util.spec_from_file_location("run_real_approval_dispatch", MODULE_PATH)


class RunRealApprovalDispatchTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_dispatch_payload_prefers_open_id_and_preserves_ids(self):
        module = self.load_module()
        payload = module.build_dispatch_payload(
            approval_code="approval-code",
            applicant_open_id="ou_123",
            tenant_access_token="tenant-token",
            task_payload={"task_id": "TASK-1"},
            goal_payload={"goal_id": "GOAL-1"},
        )
        self.assertEqual(payload["approval_code"], "approval-code")
        self.assertEqual(payload["applicant_open_id"], "ou_123")
        self.assertEqual(payload["task_payload"]["task_id"], "TASK-1")
        self.assertEqual(payload["goal_payload"]["goal_id"], "GOAL-1")

    def test_build_dispatch_result_extracts_created_instance_and_state(self):
        module = self.load_module()
        result = module.build_dispatch_result(
            dispatch_payload={
                "approval_code": "approval-code",
                "task_payload": {"task_id": "TASK-1"},
                "goal_payload": {"goal_id": "GOAL-1"},
            },
            cycle_result={
                "task_updates": {
                    "approval_instance_code": "ins_123",
                    "approval_status": "pending",
                    "automation_status": "paused",
                    "decision_summary": "approval_created",
                },
                "task_record": {"任务ID": "TASK-1"},
                "goal_record": {"目标ID": "GOAL-1"},
            },
        )
        self.assertEqual(result["approval_instance_code"], "ins_123")
        self.assertEqual(result["approval_status"], "pending")
        self.assertEqual(result["automation_status"], "paused")
        self.assertEqual(result["decision_summary"], "approval_created")


if __name__ == "__main__":
    unittest.main()

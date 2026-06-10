import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = MODULE_DIR / "run_goal_progress_approval_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_goal_progress_approval_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class RunGoalProgressApprovalCycleTests(unittest.TestCase):
    def test_creates_pending_approval_for_high_risk_task(self):
        SPEC.loader.exec_module(MODULE)
        with (
            mock.patch.object(
                MODULE.GATE,
                "evaluate_gate",
                return_value={
                    "requires_approval": True,
                    "approval_status": "pending",
                    "trigger_reason": "release_handoff",
                    "recommended_option": "recommended",
                    "options": [{"key": "recommended"}],
                    "timeout_fallback": {"action": "pause"},
                },
            ),
            mock.patch.object(
                MODULE.APPROVAL_API,
                "create_instance",
                return_value={"data": {"instance_code": "ins_001"}},
            ),
        ):
            result = MODULE.run_cycle(
                task_payload={
                    "task_id": "task-risk-001",
                    "goal_id": "goal-collab-001",
                    "risk_level": "high",
                    "change_scope": "release_handoff",
                },
                goal_payload={"goal_id": "goal-collab-001", "goal_name": "协作闭环"},
                sibling_tasks=[],
                tenant_access_token="tenant-token",
                approval_code="approval-code-001",
                applicant_user_id="ou_xxx",
            )

        self.assertEqual(result["task_updates"]["approval_status"], "pending")
        self.assertEqual(result["task_updates"]["approval_decision_id"], "task-risk-001")
        self.assertEqual(result["task_updates"]["decision_summary"], "approval_created")
        self.assertEqual(result["task_updates"]["approval_instance_code"], "ins_001")
        self.assertEqual(result["goal_record"]["goal_status"], "waiting_decision")
        self.assertEqual(result["task_record"]["审批状态"], "pending")

    def test_approved_instance_resumes_running(self):
        SPEC.loader.exec_module(MODULE)
        with (
            mock.patch.object(
                MODULE.GATE,
                "evaluate_gate",
                return_value={
                    "requires_approval": True,
                    "approval_status": "pending",
                    "trigger_reason": "release_handoff",
                    "recommended_option": "recommended",
                    "options": [{"key": "recommended"}],
                    "timeout_fallback": {"action": "pause"},
                },
            ),
            mock.patch.object(
                MODULE.APPROVAL_API,
                "get_instance",
                return_value={
                    "status": "APPROVED",
                    "instance_code": "ins_001",
                },
            ),
        ):
            result = MODULE.run_cycle(
                task_payload={
                    "task_id": "task-risk-001",
                    "goal_id": "goal-collab-001",
                    "risk_level": "high",
                    "change_scope": "release_handoff",
                    "approval_instance_code": "ins_001",
                },
                goal_payload={"goal_id": "goal-collab-001", "goal_name": "协作闭环"},
                sibling_tasks=[],
                tenant_access_token="tenant-token",
                approval_code="approval-code-001",
                applicant_user_id="ou_xxx",
            )

        self.assertEqual(result["task_updates"]["approval_status"], "approved")
        self.assertEqual(result["task_updates"]["automation_status"], "proceed")
        self.assertEqual(result["task_updates"]["decision_summary"], "approved:task-risk-001")
        self.assertEqual(result["goal_record"]["goal_status"], "active")

    def test_timeout_uses_safe_conservative_fallback_when_available(self):
        SPEC.loader.exec_module(MODULE)
        with (
            mock.patch.object(
                MODULE,
                "utc_now",
                return_value="2026-06-07T18:00:00Z",
                create=True,
            ),
            mock.patch.object(
                MODULE.GATE,
                "evaluate_gate",
                return_value={
                    "requires_approval": True,
                    "approval_status": "pending",
                    "trigger_reason": "release_handoff",
                    "recommended_option": "recommended",
                    "options": [{"key": "recommended"}],
                    "timeout_fallback": {
                        "action": "auto_continue",
                        "is_safe": True,
                        "decision_summary": "timeout:auto_continue_safe",
                    },
                },
            ),
            mock.patch.object(
                MODULE.APPROVAL_API,
                "get_instance",
                return_value={
                    "status": "PENDING",
                    "instance_code": "ins_001",
                },
            ),
        ):
            result = MODULE.run_cycle(
                task_payload={
                    "task_id": "task-risk-001",
                    "goal_id": "goal-collab-001",
                    "risk_level": "high",
                    "change_scope": "release_handoff",
                    "approval_instance_code": "ins_001",
                    "approval_due_at": "2026-06-07T17:00:00Z",
                },
                goal_payload={"goal_id": "goal-collab-001", "goal_name": "协作闭环"},
                sibling_tasks=[],
                tenant_access_token="tenant-token",
                approval_code="approval-code-001",
                applicant_user_id="ou_xxx",
            )

        self.assertEqual(result["task_updates"]["approval_status"], "timeout")
        self.assertEqual(result["task_updates"]["automation_status"], "running")
        self.assertEqual(
            result["task_updates"]["decision_summary"],
            "timeout:auto_continue_safe",
        )
        self.assertEqual(result["goal_record"]["goal_status"], "waiting_decision")

    def test_timeout_without_safe_fallback_pauses_for_manual_decision(self):
        SPEC.loader.exec_module(MODULE)
        with (
            mock.patch.object(
                MODULE,
                "utc_now",
                return_value="2026-06-07T18:00:00Z",
                create=True,
            ),
            mock.patch.object(
                MODULE.GATE,
                "evaluate_gate",
                return_value={
                    "requires_approval": True,
                    "approval_status": "pending",
                    "trigger_reason": "release_handoff",
                    "recommended_option": "recommended",
                    "options": [{"key": "recommended"}],
                    "timeout_fallback": {"action": "pause"},
                },
            ),
            mock.patch.object(
                MODULE.APPROVAL_API,
                "get_instance",
                return_value={
                    "status": "PENDING",
                    "instance_code": "ins_001",
                },
            ),
        ):
            result = MODULE.run_cycle(
                task_payload={
                    "task_id": "task-risk-001",
                    "goal_id": "goal-collab-001",
                    "risk_level": "high",
                    "change_scope": "release_handoff",
                    "approval_instance_code": "ins_001",
                    "approval_due_at": "2026-06-07T17:00:00Z",
                },
                goal_payload={"goal_id": "goal-collab-001", "goal_name": "协作闭环"},
                sibling_tasks=[],
                tenant_access_token="tenant-token",
                approval_code="approval-code-001",
                applicant_user_id="ou_xxx",
            )

        self.assertEqual(result["task_updates"]["approval_status"], "timeout")
        self.assertEqual(result["task_updates"]["automation_status"], "paused")
        self.assertEqual(
            result["task_updates"]["decision_summary"],
            "waiting_for_manual_decision",
        )
        self.assertEqual(result["goal_record"]["goal_status"], "waiting_decision")


if __name__ == "__main__":
    unittest.main()

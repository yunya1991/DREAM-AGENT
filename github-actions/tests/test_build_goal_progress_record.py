import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_goal_progress_record.py"
SPEC = importlib.util.spec_from_file_location("build_goal_progress_record", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildGoalProgressRecordTests(unittest.TestCase):
    def test_waiting_decision_goal_wins_over_active(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {
                "goal_id": "goal-collab-001",
                "goal_name": "协作闭环修复",
                "goal_owner": "governance-agent",
                "current_phase": "risk-approval",
            },
            [
                {
                    "task_id": "task-1",
                    "approval_status": "pending",
                    "platform_status": "checks_pending",
                    "governance_status": "review_required",
                    "blocker": "waiting for decision",
                    "decision_summary": "choose rollback-safe path",
                },
                {
                    "task_id": "task-2",
                    "approval_status": "not_required",
                    "platform_status": "checks_green",
                    "governance_status": "ready",
                    "blocker": "",
                    "decision_summary": "",
                },
            ],
        )
        self.assertEqual(record["goal_status"], "waiting_decision")
        self.assertEqual(record["risk_level"], "high")
        self.assertEqual(record["key_blocker"], "waiting for decision")
        self.assertEqual(record["latest_decision_summary"], "choose rollback-safe path")

    def test_released_goal_requires_all_tasks_released(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {"goal_id": "goal-release-001", "goal_name": "release"},
            [
                {
                    "task_id": "task-a",
                    "governance_status": "released",
                    "approval_status": "executed",
                },
                {
                    "task_id": "task-b",
                    "governance_status": "released",
                    "approval_status": "executed",
                },
            ],
        )
        self.assertEqual(record["goal_status"], "released")
        self.assertEqual(record["goal_progress"], 100)


if __name__ == "__main__":
    unittest.main()

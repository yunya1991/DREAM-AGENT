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

    def test_build_goal_record_emits_chinese_boss_fields(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {
                "goal_id": "goal-boss-001",
                "goal_name": "中台前端对齐",
                "goal_owner": "governance-agent",
                "current_phase": "approval-sync",
                "next_milestone": "补齐阻塞后推进联调",
            },
            [
                {
                    "task_id": "task-1",
                    "approval_status": "pending",
                    "platform_status": "checks_pending",
                    "governance_status": "review_required",
                    "blocker": "等待审批实例最终状态",
                    "decision_summary": "instance_created:188BD557-48FE-460E-8728-BD987112E7D0",
                }
            ],
        )
        self.assertEqual(record["目标名称"], "中台前端对齐")
        self.assertEqual(record["当前状态"], "等待决策")
        self.assertEqual(record["当前阻塞"], "等待审批实例最终状态")
        self.assertEqual(record["风险等级"], "high")
        self.assertEqual(record["下一步动作"], "补齐阻塞后推进联调")
        self.assertEqual(
            record["最近决策摘要"], "instance_created:188BD557-48FE-460E-8728-BD987112E7D0"
        )

    def test_goal_record_marks_missing_okr_alignment_for_active_goal(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {
                "goal_id": "goal-okr-001",
                "goal_name": "老板视图联动",
                "goal_status": "active",
                "next_milestone": "绑定 Objective",
            },
            [
                {
                    "task_id": "task-1",
                    "approval_status": "not_required",
                    "platform_status": "checks_green",
                    "governance_status": "ready",
                }
            ],
        )
        self.assertEqual(record["OKR对齐"], "待补OKR")
        self.assertEqual(record["workflow_signal"], "missing_okr_alignment")


if __name__ == "__main__":
    unittest.main()

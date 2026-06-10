import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "sync_github_to_feishu.py"
SPEC = importlib.util.spec_from_file_location("sync_github_to_feishu", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class SyncGithubToFeishuTests(unittest.TestCase):
    def test_build_module_task_record_maps_runtime_fields_to_module_task_table(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_module_task_record(
            {
                "task_id": "task-ui-map-real-data-mvt-001",
                "task_name": "MVT-1",
                "goal_id": "goal-ui-map-real-data-20260610",
                "repo": "yunya1991/Dreambuddy-V2",
                "pr_number": "12",
                "pr_url": "https://github.com/yunya1991/Dreambuddy-V2/pull/12",
                "last_comment_anchor": "https://github.com/yunya1991/Dreambuddy-V2/pull/12#issuecomment-1",
                "next_action": "继续补齐 real data override",
                "owner_agent": "SOLO",
                "automation_status": "running",
            }
        )
        self.assertEqual(record["task_id"], "task-ui-map-real-data-mvt-001")
        self.assertEqual(record["goal_id"], "goal-ui-map-real-data-20260610")
        self.assertEqual(record["status"], "in_progress")
        self.assertEqual(record["pr_number"], "12")
        self.assertEqual(record["comment_anchor"], "https://github.com/yunya1991/Dreambuddy-V2/pull/12#issuecomment-1")
        self.assertEqual(record["owner_agent"], "SOLO")

    def test_build_feishu_record_maps_all_four_status_layers(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_feishu_record(
            {
                "task_id": "task-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature",
                "pr_number": "7",
                "implementation_status": "tested",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(record["任务ID"], "task-001")
        self.assertEqual(record["平台状态"], "checks_pending")
        self.assertEqual(record["治理状态"], "review_required")
        self.assertEqual(record["自动化状态"], "running")

    def test_build_feishu_record_includes_goal_and_approval_fields(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_feishu_record(
            {
                "task_id": "task-approval-001",
                "task_name": "风险审批样例任务",
                "goal_id": "goal-collab-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature/risk-approval",
                "pr_number": "9",
                "implementation_status": "implemented",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
                "risk_level": "high",
                "approval_status": "pending",
                "approval_decision_id": "decision-001",
                "approval_due_at": "2026-06-07T16:00:00Z",
                "decision_summary": "waiting_for_choice",
            }
        )
        self.assertEqual(record["目标ID"], "goal-collab-001")
        self.assertEqual(record["风险等级"], "high")
        self.assertEqual(record["审批状态"], "pending")
        self.assertEqual(record["审批决策ID"], "decision-001")
        self.assertEqual(record["审批截止时间"], "2026-06-07T16:00:00Z")
        self.assertEqual(record["决策摘要"], "waiting_for_choice")


if __name__ == "__main__":
    unittest.main()

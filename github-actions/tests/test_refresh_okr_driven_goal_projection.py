import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "refresh_okr_driven_goal_projection.py"
SPEC = importlib.util.spec_from_file_location(
    "refresh_okr_driven_goal_projection", MODULE_PATH
)


class RefreshOkrDrivenGoalProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_refresh_marks_goal_aligned_and_risk_blocked_when_blocker_remains(self):
        module = self.load_module()
        goal = {
            "goal_id": "goal-trading-hub-connectivity-20260519",
            "goal_name": "中台与前端联动验证能力打通",
            "goal_owner": "governance-agent",
            "okr_objective_id": "7648838772720995522",
            "okr_objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
            "okr_owner": "Asher",
            "okr_sync_status": "bound",
            "okr_last_sync_at": "2026-06-08T02:14:22+00:00",
            "last_workflow_run_at": "2026-06-08T02:20:00+00:00",
        }
        tasks = [
            {
                "approval_status": "not_required",
                "governance_status": "blocked",
                "risk_level": "high",
                "blocker": "7-ARTIFACT-HUB-V2 中台尚未直连 6-TRADING",
                "decision_summary": "objective_bound:7648838772720995522",
            }
        ]
        result = module.refresh_projection(goal, tasks)
        self.assertEqual(result["OKR对齐"], "已对齐")
        self.assertEqual(result["workflow_signal"], "risk_blocked")
        self.assertEqual(result["当前状态"], "已阻塞")

    def test_refresh_emits_boss_view_verification_fields(self):
        module = self.load_module()
        goal = {
            "goal_id": "goal-trading-hub-connectivity-20260519",
            "goal_name": "中台与前端联动验证能力打通",
            "goal_owner": "governance-agent",
            "okr_objective_id": "7648838772720995522",
            "okr_objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
            "okr_owner": "Asher",
            "okr_sync_status": "bound",
            "okr_last_sync_at": "2026-06-08T02:14:22+00:00",
            "last_workflow_run_at": "2026-06-08T02:20:00+00:00",
        }
        tasks = [
            {
                "approval_status": "not_required",
                "governance_status": "blocked",
                "risk_level": "high",
                "blocker": "still blocked",
                "decision_summary": "bound",
            }
        ]
        result = module.refresh_projection(goal, tasks)
        self.assertIn("目标名称", result)
        self.assertIn("当前阻塞", result)
        self.assertIn("下一步动作", result)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "materialize_github_sync_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_github_sync_execution", MODULE_PATH)


class MaterializeGithubSyncExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "event_summary": {
                "event_type": "github.pr.changed",
                "repo": "yunya1991/DREAM-AGENT",
                "action": "synchronize",
                "number": "88",
            },
            "impacted_records": [
                {
                    "task_id": "task-github-sync-001",
                    "goal_id": "goal-collab-sync-001",
                    "repo": "yunya1991/DREAM-AGENT",
                }
            ],
            "field_updates": {
                "任务ID": "task-github-sync-001",
                "平台状态": "checks_pending",
                "自动化状态": "running",
                "治理状态": "review_required",
                "最近评论锚点": "https://github.com/yunya1991/DREAM-AGENT/pull/88#issuecomment-1",
            },
            "risk_flags": [],
            "event_coverage_hit": {
                "event_type": "github.pr.changed",
                "action": "synchronize",
                "fallback_policy": "confirmed",
            },
            "writeback_plan": [
                "event_coverage_check",
                "collab_state_writeback",
                "automation_result_writeback",
                "comment_anchor_writeback",
                "verification_snapshot",
            ],
            "requires_confirmation": True,
        }

    def test_materialize_builds_writeback_order_handoff_and_knowledge(self):
        module = self.load_module()
        result = module.materialize_github_sync_execution(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "event_coverage_check",
                "collab_state_writeback",
                "automation_result_writeback",
                "comment_anchor_writeback",
                "verification_snapshot",
            ],
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["knowledge_update"]["asset_type"], "delivery")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")

    def test_materialize_marks_soft_block_when_coverage_gap_exists(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["event_coverage_gap"]
        result = module.materialize_github_sync_execution(preview)
        self.assertEqual(result["status"], "soft_block")

    def test_materialize_marks_degraded_success_when_comment_anchor_is_missing(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["field_updates"]["最近评论锚点"] = ""
        result = module.materialize_github_sync_execution(preview)
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()

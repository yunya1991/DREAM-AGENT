import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "bitable" / "materialize_bitable_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_bitable_execution", MODULE_PATH)


class MaterializeBitableExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "task_record_candidates": [
                {
                    "task_id": "task-create-real-okr",
                    "goal_ref": "goal-trading-hub-connectivity-20260519",
                    "objective_ref": "7648838772720995522",
                    "kr_ref": "KR1",
                    "title": "创建真实 Objective 和 4 个 KR",
                    "owner": "governance-agent",
                    "status": "planned",
                    "risk_level": "medium",
                    "blocker": "",
                    "next_action": "real objective and kr ids",
                    "deliverable": "real objective and kr ids",
                    "source_refs": ["task-create-real-okr"],
                }
            ],
            "progress_record_candidates": [
                {
                    "goal_id": "goal-trading-hub-connectivity-20260519",
                    "task_ref": "task-create-real-okr",
                    "progress_status": "planned",
                    "governance_status": "planned",
                    "approval_status": "not_required",
                    "risk_level": "medium",
                    "blocker": "",
                    "decision_summary": "",
                    "last_sync_at": "",
                }
            ],
            "goal_projection_candidates": [
                {
                    "goal_id": "goal-trading-hub-connectivity-20260519",
                    "goal_name": "中台与前端联动验证能力打通",
                }
            ],
            "field_governance_report": {
                "required_fields": ["goal_id"],
                "missing_fields": [],
                "stale_fields": [],
                "field_mapping": {},
                "writeback_scope": ["tasks", "progress", "goal_projection"],
            },
            "view_projection_candidates": [
                {
                    "view_name": "老板视图（状态与阻塞）",
                    "required_columns": ["目标名称", "当前状态"],
                }
            ],
        }

    def test_materialize_builds_writeback_order_and_knowledge_update(self):
        module = self.load_module()
        result = module.materialize_bitable_execution(self.sample_preview())
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(
            result["writeback_order"],
            [
                "field_governance_check",
                "task_writeback",
                "progress_writeback",
                "goal_projection_writeback",
                "view_validation",
            ],
        )
        self.assertEqual(result["knowledge_update"]["asset_type"], "delivery")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")
        self.assertEqual(result["handoff"]["status"], "confirmed")

    def test_materialize_marks_hard_block_when_required_fields_missing(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["field_governance_report"]["missing_fields"] = ["任务标题"]
        result = module.materialize_bitable_execution(preview)
        self.assertEqual(result["status"], "hard_block")

    def test_materialize_marks_degraded_success_when_only_views_are_incomplete(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["view_projection_candidates"] = []
        result = module.materialize_bitable_execution(preview)
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()

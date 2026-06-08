import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "bitable" / "build_bitable_preview.py"
SPEC = importlib.util.spec_from_file_location("build_bitable_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "bitable_skill"


class BuildBitablePreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_payloads(self):
        return {
            "okr_preview": json.loads((FIXTURE_DIR / "okr_driven_preview.json").read_text(encoding="utf-8")),
            "base_context": json.loads((FIXTURE_DIR / "base_context.json").read_text(encoding="utf-8")),
        }

    def test_preview_builds_task_progress_projection_and_view_layers(self):
        module = self.load_module()
        preview = module.build_bitable_preview(**self.load_payloads())
        self.assertEqual(preview["requires_confirmation"], True)
        self.assertEqual(len(preview["task_record_candidates"]), 2)
        self.assertEqual(len(preview["progress_record_candidates"]), 2)
        self.assertEqual(
            preview["goal_projection_candidates"][0]["goal_id"],
            "goal-trading-hub-connectivity-20260519",
        )
        self.assertEqual(
            preview["view_projection_candidates"][0]["view_name"],
            "老板视图（状态与阻塞）",
        )

    def test_preview_marks_missing_fields_and_view_drift(self):
        module = self.load_module()
        preview = module.build_bitable_preview(
            okr_preview={
                "goal_record_candidates": [{"goal_id": "goal-1", "goal_name": "测试目标"}],
                "task_candidates": [],
                "workflow_candidates": [],
            },
            base_context={
                "required_fields": ["goal_id", "任务标题"],
                "existing_fields": ["goal_id"],
                "views": [],
            },
        )
        self.assertIn("missing_required_fields", preview["drift_flags"])
        self.assertIn("view_projection_incomplete", preview["drift_flags"])

    def test_preview_keeps_refs_linked_to_goal_and_kr(self):
        module = self.load_module()
        preview = module.build_bitable_preview(**self.load_payloads())
        first_task = preview["task_record_candidates"][0]
        self.assertEqual(first_task["goal_ref"], "goal-trading-hub-connectivity-20260519")
        self.assertTrue(first_task["kr_ref"])


if __name__ == "__main__":
    unittest.main()

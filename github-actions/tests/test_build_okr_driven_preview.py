import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_okr_driven_preview.py"
SPEC = importlib.util.spec_from_file_location("build_okr_driven_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "okr_driven_skill"


class BuildOkrDrivenPreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_sources(self):
        return {
            "spec_text": (FIXTURE_DIR / "central_hub_spec.md").read_text(encoding="utf-8"),
            "plan_text": (FIXTURE_DIR / "central_hub_plan.md").read_text(encoding="utf-8"),
        }

    def test_preview_builds_objective_kr_goal_task_workflow_layers(self):
        module = self.load_module()
        preview = module.build_preview(**self.load_sources())
        self.assertEqual(preview["requires_confirmation"], True)
        self.assertEqual(
            preview["objective_candidates"][0]["title"],
            "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
        )
        self.assertEqual(len(preview["kr_candidates"]), 4)
        self.assertEqual(
            preview["goal_record_candidates"][0]["goal_id"],
            "goal-trading-hub-connectivity-20260519",
        )
        self.assertGreaterEqual(len(preview["task_candidates"]), 1)
        self.assertGreaterEqual(len(preview["workflow_candidates"]), 1)

    def test_preview_marks_incomplete_task_or_workflow_when_plan_is_too_thin(self):
        module = self.load_module()
        preview = module.build_preview(
            spec_text="# spec\nKR1：前端关键页面完成实时联动验证\n",
            plan_text="# plan\n",
        )
        self.assertIn("task_layer_incomplete", preview["risk_flags"])
        self.assertIn("workflow_layer_incomplete", preview["risk_flags"])

    def test_preview_keeps_ids_and_refs_as_strings(self):
        module = self.load_module()
        preview = module.build_preview(**self.load_sources())
        goal = preview["goal_record_candidates"][0]
        self.assertIsInstance(goal["goal_id"], str)
        self.assertIsInstance(goal["okr_anchor_ref"], str)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "materialize_okr_driven_execution.py"
SPEC = importlib.util.spec_from_file_location(
    "materialize_okr_driven_execution", MODULE_PATH
)


class MaterializeOkrDrivenExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "objective_candidates": [
                {
                    "title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
                    "owner": "Asher",
                }
            ],
            "kr_candidates": [
                {"title": "Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路"},
                {"title": "前端关键页面完成实时联动验证，能直接反映交易链路状态变化"},
            ],
            "goal_record_candidates": [
                {
                    "goal_id": "goal-trading-hub-connectivity-20260519",
                    "goal_name": "中台与前端联动验证能力打通",
                }
            ],
            "task_candidates": [
                {
                    "task_id": "task-create-real-okr",
                    "title": "创建真实 Objective 和 4 个 KR",
                    "goal_ref": "goal-trading-hub-connectivity-20260519",
                    "kr_ref": "Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路",
                }
            ],
            "workflow_candidates": [
                {"name": "OKR对齐缺失提醒", "expected_signal": "missing_okr_alignment"}
            ],
            "requires_confirmation": True,
        }

    def test_materialize_builds_four_layer_payloads(self):
        module = self.load_module()
        result = module.materialize_execution(self.sample_preview())
        self.assertIn("okr", result)
        self.assertIn("base", result)
        self.assertIn("tasks", result)
        self.assertIn("workflow", result)
        self.assertIn("projection", result)

    def test_materialize_keeps_base_as_projection_layer(self):
        module = self.load_module()
        result = module.materialize_execution(self.sample_preview())
        self.assertEqual(result["base"]["projection_only"], True)
        self.assertEqual(result["okr"]["source_of_truth"], "feishu_okr")

    def test_materialize_requires_confirmation_before_execution(self):
        module = self.load_module()
        result = module.materialize_execution(self.sample_preview())
        self.assertEqual(result["execution_mode"], "preview_then_confirm")


if __name__ == "__main__":
    unittest.main()

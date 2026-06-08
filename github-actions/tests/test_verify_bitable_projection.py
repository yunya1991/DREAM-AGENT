import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "bitable" / "verify_bitable_projection.py"
SPEC = importlib.util.spec_from_file_location("verify_bitable_projection", MODULE_PATH)


class VerifyBitableProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_all_layers_exist(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-1"}],
            goal_projection=[{"goal_id": "goal-1", "workflow_signal": "healthy"}],
            view_validation=[{"view_name": "老板视图（状态与阻塞）"}],
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_blocked_when_goal_projection_missing(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-1"}],
            goal_projection=[],
            view_validation=[{"view_name": "老板视图（状态与阻塞）"}],
        )
        self.assertEqual(result["status"], "blocked")

    def test_verify_returns_degraded_success_when_view_layer_missing(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-1"}],
            goal_projection=[{"goal_id": "goal-1", "workflow_signal": "healthy"}],
            view_validation=[],
        )
        self.assertEqual(result["status"], "degraded_success")

    def test_verify_returns_soft_block_when_task_and_progress_refs_do_not_match(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-2"}],
            goal_projection=[{"goal_id": "goal-1", "workflow_signal": "healthy"}],
            view_validation=[{"view_name": "老板视图（状态与阻塞）"}],
        )
        self.assertEqual(result["status"], "soft_block")


if __name__ == "__main__":
    unittest.main()

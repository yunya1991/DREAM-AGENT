import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_goal_progress_approval_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_goal_progress_approval_cycle", MODULE_PATH)


class RunGoalProgressApprovalCycleContractTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_approval_form_returns_serializable_field_list(self):
        module = self.load_module()
        result = module.build_approval_form(
            task_payload={"task_id": "task-approval-001"},
            gate_result={"trigger_reason": "high_risk_scope:release_handoff"},
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "evaluate_risk_approval_gate.py"
SPEC = importlib.util.spec_from_file_location("evaluate_risk_approval_gate", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class EvaluateRiskApprovalGateTests(unittest.TestCase):
    def test_low_risk_fix_does_not_require_approval(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.evaluate_gate(
            {
                "task_id": "task-low-001",
                "risk_level": "low",
                "change_scope": "patch_fix",
                "requested_action": "continue",
            }
        )
        self.assertFalse(result["requires_approval"])
        self.assertEqual(result["approval_status"], "not_required")

    def test_release_handoff_requires_approval(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.evaluate_gate(
            {
                "task_id": "task-high-001",
                "risk_level": "high",
                "change_scope": "release_handoff",
                "requested_action": "release",
            }
        )
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["approval_status"], "pending")
        self.assertEqual(result["trigger_reason"], "release_handoff")
        self.assertEqual(result["timeout_fallback"]["action"], "pause")


if __name__ == "__main__":
    unittest.main()

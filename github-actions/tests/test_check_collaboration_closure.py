import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "check_collaboration_closure.py"
SPEC = importlib.util.spec_from_file_location(
    "check_collaboration_closure", MODULE_PATH
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CheckCollaborationClosureTests(unittest.TestCase):
    def test_blocks_ready_when_checks_are_failing(self):
        result = MODULE.evaluate_payload(
            {
                "implementation_status": "tested",
                "platform_status": "checks_failing",
                "governance_status": "ready",
                "automation_status": "running",
            }
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_GOVERNANCE_REQUIRES_GREEN_CHECKS", result["reason_codes"])

    def test_passes_review_required_when_checks_pending(self):
        result = MODULE.evaluate_payload(
            {
                "implementation_status": "tested",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["release_decision"], "hold")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "approval" / "verify_approval_projection.py"
SPEC = importlib.util.spec_from_file_location("verify_approval_projection", MODULE_PATH)


class VerifyApprovalProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_projection_and_evidence_are_complete(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={"approval_status": "approved", "automation_status": "running", "decision_summary": "approved:task-1"},
            timeout_policy={"action": "pause"},
            evidence_snapshot={"instance_code": "instance-001", "decision_summary": "approved:task-1"},
            risk_flags=[],
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_hard_block_when_status_projection_is_missing(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={},
            timeout_policy={"action": "pause"},
            evidence_snapshot={"instance_code": "instance-001", "decision_summary": "approved:task-1"},
            risk_flags=[],
        )
        self.assertEqual(result["status"], "hard_block")

    def test_verify_returns_soft_block_when_projection_gap_is_present(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={"approval_status": "pending", "automation_status": "paused", "decision_summary": "pending:task-1"},
            timeout_policy={"action": "pause"},
            evidence_snapshot={"instance_code": "instance-001", "decision_summary": "pending:task-1"},
            risk_flags=["status_projection_gap"],
        )
        self.assertEqual(result["status"], "soft_block")

    def test_verify_returns_degraded_success_when_evidence_is_missing(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={"approval_status": "approved", "automation_status": "running", "decision_summary": "approved:task-1"},
            timeout_policy={"action": "pause"},
            evidence_snapshot={},
            risk_flags=[],
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()

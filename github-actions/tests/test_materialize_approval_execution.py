import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "approval" / "materialize_approval_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_approval_execution", MODULE_PATH)


class MaterializeApprovalExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "risk_gate_summary": {
                "risk_level": "high",
                "trigger_reason": "high_risk_scope:release_handoff",
                "risk_scope": "release_handoff",
                "recommended_action": "human_review",
                "requires_approval": True,
            },
            "approval_request_candidate": {
                "approval_code": "APPROVAL-001",
                "applicant_open_id": "ou_demo_applicant",
                "instance_external_id": "task-approval-001",
                "form_payload": [{"id": "decision_id", "type": "textarea", "value": "task-approval-001"}],
                "source_refs": ["task-approval-001"],
                "target_object_id": "task-approval-001",
            },
            "status_projection_candidate": {
                "approval_status": "pending",
                "approval_decision_id": "task-approval-001",
                "decision_summary": "approval_created",
                "automation_status": "paused",
            },
            "risk_flags": [],
            "timeout_policy": {
                "action": "pause",
                "is_safe": False,
                "decision_summary": "waiting_for_manual_decision",
            },
            "requires_confirmation": True,
        }

    def test_materialize_builds_writeback_order_handoff_and_knowledge(self):
        module = self.load_module()
        result = module.materialize_approval_execution(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "risk_gate_check",
                "approval_request_writeback",
                "approval_status_projection",
                "automation_status_projection",
                "approval_evidence_snapshot",
            ],
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["knowledge_update"]["asset_type"], "operations")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")

    def test_materialize_marks_hard_block_when_approval_code_missing(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["missing_approval_code"]
        result = module.materialize_approval_execution(preview)
        self.assertEqual(result["status"], "hard_block")

    def test_materialize_marks_soft_block_when_instance_lookup_failed(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["instance_lookup_failed"]
        result = module.materialize_approval_execution(preview)
        self.assertEqual(result["status"], "soft_block")


if __name__ == "__main__":
    unittest.main()

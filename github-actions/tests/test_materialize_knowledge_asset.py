import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_knowledge_asset.py"
SPEC = importlib.util.spec_from_file_location("materialize_knowledge_asset", MODULE_PATH)


class MaterializeKnowledgeAssetTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "intake_summary": {
                "asset_type": "operations",
                "title": "Approval timeout recovery",
                "source_skill": "feishu-collab-approval",
            },
            "asset_target_candidate": {
                "target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md",
                "template_type": "runbook",
                "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
                "allow_overwrite": False,
            },
            "validation_report": {
                "title_valid": True,
                "asset_type_valid": True,
                "evidence_valid": True,
                "risk_flags": [],
            },
            "check_report": {
                "drift_flags": [],
                "gap_flags": [],
                "stale_flags": [],
                "severity": "none",
                "repair_suggestions": [],
            },
            "risk_flags": [],
            "requires_confirmation": True,
        }

    def test_materialize_builds_writeback_order_handoff_and_receipt(self):
        module = self.load_module()
        result = module.materialize_knowledge_asset(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "intake_normalization",
                "asset_target_resolution",
                "validation_snapshot",
                "knowledge_asset_writeback",
                "index_alignment_check",
            ],
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["knowledge_update"]["asset_type"], "operations")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")

    def test_materialize_marks_hard_block_for_unknown_asset_type(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["unknown_asset_type"]
        result = module.materialize_knowledge_asset(preview)
        self.assertEqual(result["status"], "hard_block")

    def test_materialize_marks_soft_block_for_index_alignment_gap(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["check_report"]["gap_flags"] = ["index_alignment_gap"]
        preview["check_report"]["severity"] = "medium"
        result = module.materialize_knowledge_asset(preview)
        self.assertEqual(result["status"], "soft_block")


if __name__ == "__main__":
    unittest.main()

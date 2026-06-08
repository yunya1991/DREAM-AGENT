import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "verify_knowledge_asset.py"
SPEC = importlib.util.spec_from_file_location("verify_knowledge_asset", MODULE_PATH)


class VerifyKnowledgeAssetTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_target_and_index_are_aligned(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md"},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": [], "stale_flags": []},
            existing_state={"target_exists": True, "index_aligned": True},
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_hard_block_when_target_missing(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": ""},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": [], "stale_flags": []},
            existing_state={"target_exists": False, "index_aligned": False},
        )
        self.assertEqual(result["status"], "hard_block")

    def test_verify_returns_soft_block_when_gap_persists(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md"},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": ["index_alignment_gap"], "stale_flags": []},
            existing_state={"target_exists": True, "index_aligned": False},
        )
        self.assertEqual(result["status"], "soft_block")

    def test_verify_returns_degraded_success_when_stale_flag_persists(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md"},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": [], "stale_flags": ["stale_source_hint"]},
            existing_state={"target_exists": True, "index_aligned": True},
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()

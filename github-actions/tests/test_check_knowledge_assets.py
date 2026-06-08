import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "check_knowledge_assets.py"
SPEC = importlib.util.spec_from_file_location("check_knowledge_assets", MODULE_PATH)


class CheckKnowledgeAssetsTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_checker_returns_clean_result_for_valid_asset(self):
        module = self.load_module()
        result = module.check_knowledge_assets(
            intake={"title": "Approval timeout recovery", "evidence_refs": ["task-approval-001"]},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            existing_state={"index_contains_target": True, "stale_hint": False},
        )
        self.assertEqual(result["severity"], "none")
        self.assertEqual(result["drift_flags"], [])
        self.assertEqual(result["gap_flags"], [])
        self.assertEqual(result["stale_flags"], [])

    def test_checker_marks_gap_when_index_missing(self):
        module = self.load_module()
        result = module.check_knowledge_assets(
            intake={"title": "Approval timeout recovery", "evidence_refs": ["task-approval-001"]},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            existing_state={"index_contains_target": False, "stale_hint": False},
        )
        self.assertIn("index_alignment_gap", result["gap_flags"])
        self.assertEqual(result["severity"], "medium")

    def test_checker_marks_stale_when_source_hint_present(self):
        module = self.load_module()
        result = module.check_knowledge_assets(
            intake={"title": "Approval timeout recovery", "evidence_refs": ["task-approval-001"]},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            existing_state={"index_contains_target": True, "stale_hint": True},
        )
        self.assertIn("stale_source_hint", result["stale_flags"])
        self.assertEqual(result["severity"], "medium")


if __name__ == "__main__":
    unittest.main()

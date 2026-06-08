import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "validate_knowledge_asset.py"
SPEC = importlib.util.spec_from_file_location("validate_knowledge_asset", MODULE_PATH)


class ValidateKnowledgeAssetTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_validation_accepts_operations_asset_with_evidence(self):
        module = self.load_module()
        result = module.validate_knowledge_asset(
            intake={
                "asset_type": "operations",
                "title": "Approval timeout recovery",
                "summary": "Manual recovery path for timed-out approvals",
                "evidence_refs": ["task-approval-001"],
            }
        )
        self.assertEqual(result["title_valid"], True)
        self.assertEqual(result["asset_type_valid"], True)
        self.assertEqual(result["evidence_valid"], True)
        self.assertEqual(result["template_type"], "runbook")

    def test_validation_marks_empty_title_as_invalid(self):
        module = self.load_module()
        result = module.validate_knowledge_asset(
            intake={
                "asset_type": "operations",
                "title": "",
                "summary": "Manual recovery path for timed-out approvals",
                "evidence_refs": ["task-approval-001"],
            }
        )
        self.assertEqual(result["title_valid"], False)
        self.assertIn("empty_title", result["risk_flags"])

    def test_validation_marks_unknown_asset_type_as_invalid(self):
        module = self.load_module()
        result = module.validate_knowledge_asset(
            intake={
                "asset_type": "mystery",
                "title": "Unknown type",
                "summary": "Should fail validation",
                "evidence_refs": ["task-approval-001"],
            }
        )
        self.assertEqual(result["asset_type_valid"], False)
        self.assertIn("unknown_asset_type", result["risk_flags"])


if __name__ == "__main__":
    unittest.main()

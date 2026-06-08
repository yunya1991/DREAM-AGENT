import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "intake.py"
SPEC = importlib.util.spec_from_file_location("knowledge_intake", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "knowledge_ops"


class KnowledgeIntakeTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_normalize_knowledge_intake_preserves_source_skill_and_handoff(self):
        module = self.load_module()
        result = module.normalize_knowledge_intake(
            knowledge_update=self.load_fixture("knowledge_update.json"),
            handoff_context=self.load_fixture("handoff_context.json"),
        )
        self.assertEqual(result["asset_type"], "operations")
        self.assertEqual(result["title"], "Approval timeout recovery")
        self.assertEqual(result["source_skill"], "feishu-collab-approval")
        self.assertEqual(
            result["handoff_summary"],
            "Approval timed out and needs manual review",
        )

    def test_normalize_knowledge_intake_defaults_missing_handoff_summary(self):
        module = self.load_module()
        result = module.normalize_knowledge_intake(
            knowledge_update=self.load_fixture("knowledge_update.json"),
            handoff_context={},
        )
        self.assertEqual(result["handoff_summary"], "")


if __name__ == "__main__":
    unittest.main()

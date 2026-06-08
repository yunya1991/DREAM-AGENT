import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "pathing.py"
SPEC = importlib.util.spec_from_file_location("feishu_collab_knowledge_pathing", MODULE_PATH)
DOC_ROOT = ROOT / "docs" / "feishu-collab"


class FeishuCollabKnowledgePathingTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_operations_updates_route_to_runbooks_directory(self):
        module = self.load_module()
        target = module.resolve_knowledge_target("operations", "approval timeout")
        self.assertEqual(
            target,
            "docs/feishu-collab/runbooks/approval-timeout.md",
        )

    def test_delivery_updates_route_to_handoffs_directory(self):
        module = self.load_module()
        target = module.resolve_knowledge_target("delivery", "okr-driven checkpoint")
        self.assertEqual(
            target,
            "docs/feishu-collab/handoffs/okr-driven-checkpoint.md",
        )

    def test_templates_exist(self):
        self.assertTrue((DOC_ROOT / "templates" / "handoff-template.md").exists())
        self.assertTrue((DOC_ROOT / "templates" / "runbook-template.md").exists())


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_real_knowledge_materialization_summary.py"
SPEC = importlib.util.spec_from_file_location(
    "render_real_knowledge_materialization_summary",
    MODULE_PATH,
)


class RenderRealKnowledgeMaterializationSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_result(self, status="success", index_status="success"):
        return {
            "materialization_status": status,
            "source_refs": {
                "task_id": "TASK-123",
                "goal_id": "GOAL-123",
                "approval_instance_code": "ins_123",
            },
            "runbook": {
                "target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
            },
            "handoff": {
                "target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
            },
            "index_update_status": index_status,
        }

    def test_summary_renders_core_paths_and_status(self):
        module = self.load_module()
        summary = module.build_summary_markdown(self.sample_result())
        self.assertIn("TASK-123", summary)
        self.assertIn("GOAL-123", summary)
        self.assertIn("ins_123", summary)
        self.assertIn("approval-task-123-runbook.md", summary)
        self.assertIn("approval-task-123-handoff.md", summary)
        self.assertIn("success", summary)

    def test_exit_code_requires_full_success(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_result()), 0)
        self.assertEqual(module.workflow_exit_code(self.sample_result(status="failed")), 1)
        self.assertEqual(module.workflow_exit_code(self.sample_result(index_status="skipped")), 1)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "event_coverage_registry.json"
MODULE_PATH = ROOT / "github-actions" / "sync_github_to_feishu.py"
SPEC = importlib.util.spec_from_file_location("sync_github_to_feishu", MODULE_PATH)


class GithubSyncRegistryTests(unittest.TestCase):
    def load_registry(self):
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_registry_covers_issue_pr_and_check_events(self):
        registry = self.load_registry()
        covered = {item["event_type"] for item in registry["events"]}
        self.assertEqual(
            covered,
            {"github.issue.changed", "github.pr.changed", "github.check.changed"},
        )

    def test_registry_declares_fallback_policy_for_every_event(self):
        registry = self.load_registry()
        for item in registry["events"]:
            self.assertTrue(item["fallback_policy"])
            self.assertTrue(item["supported_actions"])
            self.assertTrue(item["field_mapping"])

    def test_sync_module_exposes_projection_adapter(self):
        module = self.load_module()
        record = module.project_github_collab_state(
            {
                "task_id": "task-001",
                "task_name": "Sync preview",
                "goal_id": "goal-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature/test",
                "pr_number": "8",
                "workflow_run_id": "99",
                "implementation_status": "implemented",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(record["任务ID"], "task-001")
        self.assertEqual(record["平台状态"], "checks_pending")
        self.assertEqual(record["自动化状态"], "running")


if __name__ == "__main__":
    unittest.main()

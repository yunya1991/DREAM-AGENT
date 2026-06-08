import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "build_github_sync_preview.py"
SPEC = importlib.util.spec_from_file_location("build_github_sync_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "github_sync"


class BuildGithubSyncPreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_preview_builds_pr_event_summary_and_field_updates(self):
        module = self.load_module()
        preview = module.build_github_sync_preview(
            event_payload=self.load_fixture("pr_event.json"),
            collab_context=self.load_fixture("collab_context.json"),
        )
        self.assertEqual(preview["event_summary"]["event_type"], "github.pr.changed")
        self.assertEqual(preview["event_summary"]["repo"], "yunya1991/DREAM-AGENT")
        self.assertEqual(preview["field_updates"]["平台状态"], "checks_pending")
        self.assertEqual(preview["field_updates"]["自动化状态"], "running")
        self.assertEqual(preview["event_coverage_hit"]["action"], "synchronize")
        self.assertEqual(preview["requires_confirmation"], True)

    def test_preview_marks_issue_event_without_goal_link_as_risk(self):
        module = self.load_module()
        context = self.load_fixture("collab_context.json")
        context["goal_id"] = ""
        preview = module.build_github_sync_preview(
            event_payload=self.load_fixture("issue_event.json"),
            collab_context=context,
        )
        self.assertIn("missing_goal_link", preview["risk_flags"])
        self.assertEqual(preview["event_summary"]["event_type"], "github.issue.changed")

    def test_preview_marks_unknown_check_state_as_coverage_gap(self):
        module = self.load_module()
        event_payload = self.load_fixture("check_event.json")
        event_payload["check_run"]["conclusion"] = "startup_failure"
        preview = module.build_github_sync_preview(
            event_payload=event_payload,
            collab_context=self.load_fixture("collab_context.json"),
        )
        self.assertIn("unknown_check_state", preview["risk_flags"])
        self.assertEqual(preview["event_coverage_hit"]["fallback_policy"], "soft_block")


if __name__ == "__main__":
    unittest.main()

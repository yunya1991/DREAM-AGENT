import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "verify_github_sync_projection.py"
SPEC = importlib.util.spec_from_file_location("verify_github_sync_projection", MODULE_PATH)


class VerifyGithubSyncProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_fields_and_coverage_are_complete(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "task-1", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.pr.changed", "action": "synchronize"},
            risk_flags=[],
            comment_anchor="https://github.com/example/pull/1#issuecomment-1",
            automation_summary={"status": "running"},
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_hard_block_when_task_record_is_missing(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.pr.changed", "action": "synchronize"},
            risk_flags=[],
            comment_anchor="https://github.com/example/pull/1#issuecomment-1",
            automation_summary={"status": "running"},
        )
        self.assertEqual(result["status"], "hard_block")

    def test_verify_returns_soft_block_when_coverage_gap_is_present(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "task-1", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.check.changed", "action": "completed"},
            risk_flags=["event_coverage_gap"],
            comment_anchor="https://github.com/example/pull/1#issuecomment-1",
            automation_summary={"status": "completed"},
        )
        self.assertEqual(result["status"], "soft_block")

    def test_verify_returns_degraded_success_when_comment_anchor_is_missing(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "task-1", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.pr.changed", "action": "synchronize"},
            risk_flags=[],
            comment_anchor="",
            automation_summary={"status": "running"},
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()

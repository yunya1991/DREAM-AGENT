import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "sync_github_to_feishu.py"
SPEC = importlib.util.spec_from_file_location("sync_github_to_feishu", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class SyncGithubToFeishuTests(unittest.TestCase):
    def test_build_feishu_record_maps_all_four_status_layers(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_feishu_record(
            {
                "task_id": "task-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature",
                "pr_number": "7",
                "implementation_status": "tested",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(record["任务ID"], "task-001")
        self.assertEqual(record["平台状态"], "checks_pending")
        self.assertEqual(record["治理状态"], "review_required")
        self.assertEqual(record["自动化状态"], "running")


if __name__ == "__main__":
    unittest.main()

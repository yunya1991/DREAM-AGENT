import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "process_feishu_remote_action.py"
SPEC = importlib.util.spec_from_file_location("process_feishu_remote_action", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProcessFeishuRemoteActionTests(unittest.TestCase):
    def test_pause_action_sets_paused_status(self):
        result = MODULE.apply_remote_action(
            {"automation_status": "running"},
            {"remote_action": "pause"},
        )
        self.assertEqual(result["automation_status"], "paused")
        self.assertEqual(result["remote_action_result"], "pause_applied")
        self.assertEqual(result["remote_action"], "none")

    def test_retry_action_sets_retry_triggered(self):
        result = MODULE.apply_remote_action(
            {"automation_status": "failed"},
            {"remote_action": "retry"},
        )
        self.assertEqual(result["automation_status"], "running")
        self.assertEqual(result["remote_action_result"], "retry_triggered")
        self.assertEqual(result["remote_action"], "none")


if __name__ == "__main__":
    unittest.main()

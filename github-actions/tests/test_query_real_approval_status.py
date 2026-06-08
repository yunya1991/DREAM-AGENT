import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "query_real_approval_status.py"
SPEC = importlib.util.spec_from_file_location("query_real_approval_status", MODULE_PATH)


class QueryRealApprovalStatusTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_status_result_uses_status_projection(self):
        module = self.load_module()
        result = module.build_status_result(
            instance={"status": "APPROVED"},
            decision_id="TASK-1",
            instance_code="ins_123",
        )
        self.assertEqual(result["approval_instance_code"], "ins_123")
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["automation_status"], "running")
        self.assertEqual(result["decision_summary"], "approved:TASK-1")


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_approval_api.py"
SPEC = importlib.util.spec_from_file_location("feishu_approval_api", MODULE_PATH)


class FeishuApprovalApiContractTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_create_instance_body_uses_open_id_and_json_string_form(self):
        module = self.load_module()
        body = module.build_create_instance_body(
            approval_code="APPROVAL-001",
            applicant_open_id="ou_demo_applicant",
            instance_external_id="task-approval-001",
            form=[{"id": "decision_id", "type": "textarea", "value": "task-approval-001"}],
        )
        self.assertEqual(body["approval_code"], "APPROVAL-001")
        self.assertEqual(body["open_id"], "ou_demo_applicant")
        self.assertIsInstance(body["form"], str)
        self.assertNotIn("user_id", body)

    def test_build_status_projection_keeps_instance_code(self):
        module = self.load_module()
        projection = module.build_status_projection(
            instance={"status": "APPROVED"},
            decision_id="task-approval-001",
            instance_code="instance-001",
        )
        self.assertEqual(projection["approval_status"], "approved")
        self.assertEqual(projection["approval_instance_code"], "instance-001")


if __name__ == "__main__":
    unittest.main()

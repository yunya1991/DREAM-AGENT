import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_approval_api.py"
SPEC = importlib.util.spec_from_file_location("feishu_approval_api", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class FeishuApprovalApiTests(unittest.TestCase):
    def test_build_create_instance_body_keeps_external_id_and_form(self):
        SPEC.loader.exec_module(MODULE)
        body = MODULE.build_create_instance_body(
            approval_code="approval-code-001",
            user_id="ou_xxx",
            instance_external_id="decision-001",
            form=[{"id": "decision_summary", "type": "textarea", "value": "pick A"}],
        )
        self.assertEqual(body["approval_code"], "approval-code-001")
        self.assertEqual(body["user_id"], "ou_xxx")
        self.assertEqual(body["instance_external_id"], "decision-001")
        self.assertEqual(body["form"][0]["value"], "pick A")

    @mock.patch("urllib.request.urlopen")
    def test_create_instance_uses_instances_endpoint(self, mock_urlopen):
        SPEC.loader.exec_module(MODULE)
        mock_urlopen.return_value.__enter__.return_value = io.BytesIO(
            json.dumps({"data": {"instance_code": "ins_001"}}).encode("utf-8")
        )
        result = MODULE.create_instance(
            tenant_access_token="tenant-token",
            body={"approval_code": "approval-code-001"},
        )
        self.assertEqual(result["data"]["instance_code"], "ins_001")
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(
            request.full_url,
            "https://open.feishu.cn/open-apis/approval/v4/instances",
        )
        self.assertEqual(request.get_method(), "POST")

    def test_resolve_instance_status_maps_to_task_updates(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.resolve_instance_status(
            {
                "status": "APPROVED",
                "instance_code": "ins_001",
            },
            decision_id="decision-001",
        )
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["automation_status"], "running")
        self.assertEqual(result["decision_summary"], "approved:decision-001")


if __name__ == "__main__":
    unittest.main()

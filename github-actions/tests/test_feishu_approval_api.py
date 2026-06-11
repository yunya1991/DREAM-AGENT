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
    def test_build_create_instance_body_keeps_external_id_and_serializes_form(self):
        SPEC.loader.exec_module(MODULE)
        body = MODULE.build_create_instance_body(
            approval_code="approval-code-001",
            applicant_open_id="ou_xxx",
            instance_external_id="decision-001",
            form=[{"id": "decision_summary", "type": "textarea", "value": "pick A"}],
        )
        self.assertEqual(body["approval_code"], "approval-code-001")
        self.assertEqual(body["open_id"], "ou_xxx")
        self.assertEqual(body["instance_external_id"], "decision-001")
        self.assertEqual(
            body["form"],
            json.dumps(
                [{"id": "decision_summary", "type": "textarea", "value": "pick A"}],
                ensure_ascii=False,
            ),
        )

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

    def test_resolve_instance_status_maps_to_normalized_automation_states(self):
        SPEC.loader.exec_module(MODULE)
        approved = MODULE.resolve_instance_status({"status": "APPROVED"}, decision_id="decision-001")
        rejected = MODULE.resolve_instance_status({"status": "REJECTED"}, decision_id="decision-002")
        pending = MODULE.resolve_instance_status({"status": "PENDING"}, decision_id="decision-003")

        self.assertEqual(approved["approval_status"], "approved")
        self.assertEqual(approved["automation_status"], "running")
        self.assertEqual(approved["decision_summary"], "approved:decision-001")

        self.assertEqual(rejected["approval_status"], "rejected")
        self.assertEqual(rejected["automation_status"], "blocked")
        self.assertEqual(rejected["decision_summary"], "rejected:decision-002")

        self.assertEqual(pending["approval_status"], "pending")
        self.assertEqual(pending["automation_status"], "paused")
        self.assertEqual(pending["decision_summary"], "pending:decision-003")


if __name__ == "__main__":
    unittest.main()

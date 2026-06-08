import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "approval" / "build_approval_preview.py"
SPEC = importlib.util.spec_from_file_location("build_approval_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "approval_skill"


class BuildApprovalPreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_preview_builds_gate_summary_request_candidate_and_timeout_policy(self):
        module = self.load_module()
        preview = module.build_approval_preview(
            risk_context=self.load_fixture("risk_context.json"),
            approval_context=self.load_fixture("approval_context.json"),
        )
        self.assertEqual(preview["risk_gate_summary"]["requires_approval"], True)
        self.assertEqual(preview["risk_gate_summary"]["trigger_reason"], "high_risk_scope:release_handoff")
        self.assertEqual(preview["approval_request_candidate"]["approval_code"], "APPROVAL-001")
        self.assertEqual(preview["approval_request_candidate"]["applicant_open_id"], "ou_demo_applicant")
        self.assertEqual(preview["timeout_policy"]["action"], "pause")
        self.assertEqual(preview["requires_confirmation"], True)

    def test_preview_marks_missing_approval_code_as_risk(self):
        module = self.load_module()
        context = self.load_fixture("approval_context.json")
        context["approval_code"] = ""
        preview = module.build_approval_preview(
            risk_context=self.load_fixture("risk_context.json"),
            approval_context=context,
        )
        self.assertIn("missing_approval_code", preview["risk_flags"])

    def test_preview_marks_missing_applicant_open_id_as_risk(self):
        module = self.load_module()
        context = self.load_fixture("approval_context.json")
        context["applicant_open_id"] = ""
        preview = module.build_approval_preview(
            risk_context=self.load_fixture("risk_context.json"),
            approval_context=context,
        )
        self.assertIn("missing_applicant_open_id", preview["risk_flags"])


if __name__ == "__main__":
    unittest.main()

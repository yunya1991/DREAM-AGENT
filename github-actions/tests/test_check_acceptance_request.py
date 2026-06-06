import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[1] / "check_acceptance_request.py"
SPEC = importlib.util.spec_from_file_location("check_acceptance_request", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


VALID_COMMENT = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-001
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #4

## 验收对象
- PR comment driven acceptance pilot

## 验收范围
- comment structure

## 业务上下文映射
- 架构图基线: http://127.0.0.1:62932/ui-map-independent-hub-architecture.html
- 前端承接基线: http://localhost:3000/dashboard

## 重点验收项
- source of truth clarity

## 本轮不要求
- no business code changes

## 期望回写格式
- 验收对象
- 最终结论
""".strip()


class AcceptanceRequestTemplateTests(unittest.TestCase):
    def test_acceptance_request_template_exists_and_declares_required_sections(self):
        template = ROOT / "templates" / "pr-comment-acceptance-request.md"
        self.assertTrue(template.exists(), str(template))
        text = template.read_text(encoding="utf-8")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", text)
        self.assertIn("Acceptance Request ID:", text)
        self.assertIn("## 验收对象", text)
        self.assertIn("## 验收范围", text)
        self.assertIn("## 业务上下文映射", text)
        self.assertIn("## 重点验收项", text)
        self.assertIn("## 本轮不要求", text)
        self.assertIn("## 期望回写格式", text)


class ValidationResultTemplateTests(unittest.TestCase):
    def test_validation_result_template_supports_acceptance_mode_fields(self):
        template = ROOT / "templates" / "pr-comment-validation-result.md"
        text = template.read_text(encoding="utf-8")
        self.assertIn("Validation Mode:", text)
        self.assertIn("Acceptance Request ID:", text)
        self.assertIn("Protocol Read Result:", text)
        self.assertIn("Source of Truth Verdict:", text)
        self.assertIn("Must-Fix Items:", text)
        self.assertIn("Next Step Recommendation:", text)
        self.assertIn("Acceptance Conclusion:", text)


class AcceptanceRequestParserTests(unittest.TestCase):
    def test_acceptance_request_passes_when_required_fields_and_sections_exist(self):
        result = MODULE.evaluate_acceptance_request(VALID_COMMENT)
        self.assertEqual(result["decision"], "ACCEPTED")
        self.assertEqual(result["protocol_read_result"], "PASS")
        self.assertEqual(result["source_of_truth_verdict"], "usable")

    def test_acceptance_request_returns_rework_when_required_section_is_missing(self):
        broken = VALID_COMMENT.replace("## 重点验收项\n- source of truth clarity\n\n", "")
        result = MODULE.evaluate_acceptance_request(broken)
        self.assertEqual(result["decision"], "REWORK")
        self.assertIn("RULE_ACCEPTANCE_SECTION_MISSING", result["reason_codes"])

    def test_acceptance_request_returns_block_when_anchor_is_missing(self):
        broken = VALID_COMMENT.replace("[验收委托 / ACCEPTANCE_REQUEST]", "[别的评论]")
        result = MODULE.evaluate_acceptance_request(broken)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_ACCEPTANCE_ANCHOR_MISSING", result["reason_codes"])


if __name__ == "__main__":
    unittest.main()

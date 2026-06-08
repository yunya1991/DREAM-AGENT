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
Acceptance Cycle ID: ac-20260607-001
Work Item ID: WI-123
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #6
Lark Base URL: https://example.feishu.cn/base/app123?table=tbl456
Lark Table ID: tbl456
Lark Record ID: rec789

## 验收对象
- PR comment driven acceptance pilot

## 验收范围
- comment structure

## 业务上下文映射
- 目标来源: Objective O-1 / KR KR-1
- 本轮说明: verify cycle orchestration inputs

## 重点验收项
- source of truth clarity

## 本轮不要求
- no business code changes

## 期望回写格式
- 验收对象
- 协议读取结论
- 当前阻塞项
- 下一步建议
- 最终结论
""".strip()


class AcceptanceRequestTemplateTests(unittest.TestCase):
    def test_acceptance_request_template_exists_and_declares_required_sections(self):
        template = ROOT / "templates" / "pr-comment-acceptance-request.md"
        self.assertTrue(template.exists(), str(template))
        text = template.read_text(encoding="utf-8")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", text)
        self.assertIn("Acceptance Request ID:", text)
        self.assertIn("Acceptance Cycle ID:", text)
        self.assertIn("Work Item ID:", text)
        self.assertIn("Lark Base URL:", text)
        self.assertIn("Lark Table ID:", text)
        self.assertIn("Lark Record ID:", text)
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
        self.assertIn("Acceptance Cycle ID:", text)
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

    def test_acceptance_request_extracts_cycle_and_lark_locators(self):
        result = MODULE.evaluate_acceptance_request(VALID_COMMENT)
        self.assertEqual(result["decision"], "ACCEPTED")
        self.assertEqual(result["acceptance_request_id"], "ar-20260607-001")
        self.assertEqual(result["acceptance_cycle_id"], "ac-20260607-001")
        self.assertEqual(result["work_item_id"], "WI-123")
        self.assertEqual(result["lark_table_id"], "tbl456")
        self.assertEqual(result["lark_record_id"], "rec789")

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


class AcceptanceProtocolDocsTests(unittest.TestCase):
    def test_collaboration_protocol_mentions_acceptance_request_anchor(self):
        text = (ROOT / "docs" / "01-COLLABORATION-PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", text)
        self.assertIn("DONE != ACCEPTED", text)
        self.assertIn("Acceptance Cycle ID", text)
        self.assertIn("Work Item ID", text)
        self.assertIn("Lark Base URL", text)
        self.assertIn("Lark Table ID", text)
        self.assertIn("Lark Record ID", text)

    def test_workflow_norms_mentions_precheck_rule(self):
        text = (ROOT / "docs" / "03-WORKFLOWS-AND-NORMS.md").read_text(encoding="utf-8")
        self.assertIn("先读取最近一次 `VALIDATION_RESULT`", text)
        self.assertIn("ACCEPTANCE_REQUEST", text)


if __name__ == "__main__":
    unittest.main()

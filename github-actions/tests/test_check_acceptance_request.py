import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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


if __name__ == "__main__":
    unittest.main()

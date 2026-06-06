import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[1] / "resolve_acceptance_inputs.py"
SPEC = importlib.util.spec_from_file_location("resolve_acceptance_inputs", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


COMMENT_BODY = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-003
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #6

## 验收对象
- 验证多行评论输入也能被安全读取
""".strip()


class ResolveAcceptanceInputsTests(unittest.TestCase):
    def test_extracts_pr_number_and_request_id_from_issue_comment_event(self):
        event = {
            "issue": {
                "number": 6,
                "pull_request": {"url": "https://api.github.com/repos/yunya1991/DREAM-AGENT/pulls/6"},
            },
            "comment": {"body": COMMENT_BODY},
        }

        result = MODULE.resolve_issue_comment_event(event)

        self.assertEqual(result["pr_number"], "6")
        self.assertEqual(result["acceptance_request_id"], "ar-20260607-003")
        self.assertEqual(result["comment_body"], COMMENT_BODY)

    def test_loads_issue_comment_event_from_github_event_path(self):
        event = {
            "issue": {
                "number": 8,
                "pull_request": {"url": "https://api.github.com/repos/yunya1991/DREAM-AGENT/pulls/8"},
            },
            "comment": {"body": COMMENT_BODY.replace("ar-20260607-003", "ar-20260607-008")},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = Path(tmpdir) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8")

            result = MODULE.resolve_issue_comment_event_path(event_path)

        self.assertEqual(result["pr_number"], "8")
        self.assertEqual(result["acceptance_request_id"], "ar-20260607-008")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", result["comment_body"])


if __name__ == "__main__":
    unittest.main()

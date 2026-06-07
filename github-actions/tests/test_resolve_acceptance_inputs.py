import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[1] / "resolve_acceptance_inputs.py"
SPEC = importlib.util.spec_from_file_location("resolve_acceptance_inputs", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


COMMENT_BODY = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-003
Acceptance Cycle ID: ac-20260607-003
Work Item ID: WI-123
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #6
Lark Base URL: https://example.feishu.cn/base/app123?table=tbl456
Lark Table ID: tbl456
Lark Record ID: rec789

## 验收对象
- 验证多行评论输入也能被安全读取
""".strip()


class ResolveAcceptanceInputsTests(unittest.TestCase):
    def test_extract_field_reads_cycle_and_work_item_ids_from_comment_body(self):
        self.assertEqual(
            MODULE.extract_field(COMMENT_BODY, "Acceptance Cycle ID"),
            "ac-20260607-003",
        )
        self.assertEqual(MODULE.extract_field(COMMENT_BODY, "Work Item ID"), "WI-123")

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
        self.assertEqual(result["acceptance_cycle_id"], "ac-20260607-003")
        self.assertEqual(result["work_item_id"], "WI-123")
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
        self.assertEqual(result["acceptance_cycle_id"], "ac-20260607-003")
        self.assertEqual(result["work_item_id"], "WI-123")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", result["comment_body"])

    def test_main_writes_outputs_from_github_event_path(self):
        event = {
            "issue": {
                "number": 9,
                "pull_request": {"url": "https://api.github.com/repos/yunya1991/DREAM-AGENT/pulls/9"},
            },
            "comment": {"body": COMMENT_BODY.replace("ar-20260607-003", "ar-20260607-009")},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = Path(tmpdir) / "event.json"
            output_path = Path(tmpdir) / "github_output.txt"
            event_path.write_text(json.dumps(event), encoding="utf-8")

            with mock.patch.dict(
                os.environ,
                {
                    "GITHUB_EVENT_PATH": str(event_path),
                    "GITHUB_OUTPUT": str(output_path),
                },
                clear=False,
            ):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    MODULE.main()

            output = output_path.read_text(encoding="utf-8")

        self.assertIn("pr_number=9", output)
        self.assertIn("acceptance_request_id=ar-20260607-009", output)
        self.assertIn("acceptance_cycle_id=ac-20260607-003", output)
        self.assertIn("work_item_id=WI-123", output)


if __name__ == "__main__":
    unittest.main()

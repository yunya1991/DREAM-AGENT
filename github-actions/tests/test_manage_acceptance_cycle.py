import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

MODULE_PATH = MODULE_DIR / "manage_acceptance_cycle.py"
SPEC = importlib.util.spec_from_file_location("manage_acceptance_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AcceptanceCycleLedgerTests(unittest.TestCase):
    def test_create_manual_cycle_writes_record_and_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ledger_dir = root / "ledger" / "acceptance_cycles"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "index.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "",
                        "open_cycles": [],
                        "cycles": [],
                    }
                ),
                encoding="utf-8",
            )

            record = MODULE.create_manual_cycle(
                root=root,
                acceptance_cycle_id="ac-20260607-001",
                work_item_id="WI-123",
                pr_number="6",
                acceptance_request_id="ar-20260607-006",
                lark_base_url="https://example.feishu.cn/base/app123?table=tbl456",
                lark_table_id="tbl456",
                lark_record_id="rec789",
            )

            self.assertEqual(record["cycle_status"], "requested")
            self.assertEqual(record["current_phase"], "context-reader")
            self.assertEqual(record["linked_prs"], ["6"])
            self.assertEqual(record["lark_context_locator"]["record_id"], "rec789")

            persisted = json.loads(
                (ledger_dir / "ac-20260607-001.json").read_text(encoding="utf-8")
            )
            index_payload = json.loads(
                (ledger_dir / "index.json").read_text(encoding="utf-8")
            )

            self.assertEqual(persisted["acceptance_cycle_id"], "ac-20260607-001")
            self.assertIn("ac-20260607-001", index_payload["open_cycles"])
            self.assertEqual(
                index_payload["cycles"][0]["acceptance_cycle_id"], "ac-20260607-001"
            )

    def test_update_cycle_phase_keeps_latest_request_pointer(self):
        cycle = {
            "acceptance_cycle_id": "ac-20260607-001",
            "cycle_status": "requested",
            "current_phase": "context-reader",
            "latest_acceptance_request_id": "ar-20260607-006",
            "latest_validation_result_id": "",
            "agent_outputs": {},
        }

        updated = MODULE.apply_cycle_progress(
            cycle,
            phase="result-synthesizer",
            cycle_status="validated",
            validation_result_id="vr-20260607-001",
            agent_output={"decision": "ACCEPTED"},
        )

        self.assertEqual(updated["current_phase"], "result-synthesizer")
        self.assertEqual(updated["cycle_status"], "validated")
        self.assertEqual(
            updated["latest_acceptance_request_id"], "ar-20260607-006"
        )
        self.assertEqual(updated["latest_validation_result_id"], "vr-20260607-001")
        self.assertEqual(
            updated["agent_outputs"]["result-synthesizer"]["decision"], "ACCEPTED"
        )

    def test_main_creates_cycle_from_comment_body_and_prints_json(self):
        comment_body = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-006
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

## 重点验收项
- source of truth clarity

## 本轮不要求
- no business code changes

## 期望回写格式
- 最终结论
""".strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ledger_dir = root / "ledger" / "acceptance_cycles"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "index.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "",
                        "open_cycles": [],
                        "cycles": [],
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {
                    "GITHUB_WORKSPACE": str(root),
                    "PR_NUMBER": "6",
                    "ACCEPTANCE_REQUEST_ID": "ar-20260607-006",
                    "COMMENT_BODY": comment_body,
                },
                clear=False,
            ):
                with mock.patch("sys.stdout", new=stdout):
                    MODULE.main()

            payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["acceptance_cycle_id"], "ac-20260607-001")
        self.assertEqual(payload["work_item_id"], "WI-123")
        self.assertEqual(payload["lark_context_locator"]["record_id"], "rec789")


if __name__ == "__main__":
    unittest.main()

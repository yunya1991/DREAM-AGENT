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

MODULE_PATH = MODULE_DIR / "run_acceptance_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_acceptance_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RunAcceptanceCycleTests(unittest.TestCase):
    @mock.patch.object(MODULE, "collect_context_snapshot")
    @mock.patch.object(MODULE, "evaluate_acceptance_request")
    def test_run_cycle_executes_serial_roles_and_builds_outputs(
        self,
        mock_evaluate,
        mock_collect,
    ):
        mock_collect.return_value = {
            "work_item": {"record_id": "rec789", "fields": {"Title": "Pilot item"}},
            "objective": {"id": "obj1"},
            "key_result": {"id": "kr1"},
            "context_summary": "Pilot item",
        }
        mock_evaluate.return_value = {
            "decision": "ACCEPTED",
            "protocol_read_result": "PASS",
            "source_of_truth_verdict": "usable",
            "reason_codes": ["NONE"],
            "recommended_next_action": "validator: post VALIDATION_RESULT",
            "acceptance_request_id": "ar-20260607-006",
            "acceptance_cycle_id": "ac-20260607-001",
            "work_item_id": "WI-123",
        }

        result = MODULE.run_cycle(
            cycle={
                "acceptance_cycle_id": "ac-20260607-001",
                "work_item_id": "WI-123",
                "current_phase": "context-reader",
                "cycle_status": "requested",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            },
            comment_body="[验收委托 / ACCEPTANCE_REQUEST]",
            pr_number="6",
        )

        self.assertEqual(result["cycle"]["cycle_status"], "validated")
        self.assertEqual(result["cycle"]["current_phase"], "result-synthesizer")
        self.assertEqual(result["validation_result"]["decision"], "ACCEPTED")
        self.assertIn("Acceptance Cycle ID: ac-20260607-001", result["comment_body"])
        self.assertEqual(
            result["lark_summary_patch"]["fields"]["Acceptance Status"], "accepted"
        )
        self.assertIn("- objective_id=obj1", result["comment_body"])
        self.assertIn("- key_result_id=kr1", result["comment_body"])

    def test_build_validation_result_comment_renders_okr_summary_when_available(self):
        comment = MODULE.build_validation_result_comment(
            cycle={
                "acceptance_cycle_id": "ac-20260607-001",
                "linked_prs": ["7"],
            },
            validation_result={
                "decision": "ACCEPTED",
                "acceptance_request_id": "ar-20260607-006",
                "protocol_read_result": "PASS",
                "source_of_truth_verdict": "usable",
                "reason_codes": ["NONE"],
                "recommended_next_action": "validator: post VALIDATION_RESULT",
            },
            context_snapshot={
                "context_summary": "Pilot item",
                "objective": {"id": "obj1", "name": "Improve collaboration"},
                "key_result": {"id": "kr1", "name": "Reduce reruns"},
            },
        )

        self.assertIn("- objective_id=obj1", comment)
        self.assertIn("- objective_title=Improve collaboration", comment)
        self.assertIn("- key_result_id=kr1", comment)
        self.assertIn("- key_result_title=Reduce reruns", comment)

    @mock.patch.object(MODULE, "collect_context_snapshot")
    @mock.patch.object(MODULE, "evaluate_acceptance_request")
    def test_run_cycle_does_not_duplicate_existing_pr_number(
        self,
        mock_evaluate,
        mock_collect,
    ):
        mock_collect.return_value = {
            "work_item": {"record_id": "rec789", "fields": {"Title": "Pilot item"}},
            "objective": {},
            "key_result": {},
            "context_summary": "Pilot item",
        }
        mock_evaluate.return_value = {
            "decision": "ACCEPTED",
            "protocol_read_result": "PASS",
            "source_of_truth_verdict": "usable",
            "reason_codes": ["NONE"],
            "recommended_next_action": "validator: post VALIDATION_RESULT",
            "acceptance_request_id": "ar-20260607-006",
            "acceptance_cycle_id": "ac-20260607-001",
            "work_item_id": "WI-123",
        }

        result = MODULE.run_cycle(
            cycle={
                "acceptance_cycle_id": "ac-20260607-001",
                "work_item_id": "WI-123",
                "current_phase": "context-reader",
                "cycle_status": "requested",
                "linked_prs": ["6"],
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            },
            comment_body="[验收委托 / ACCEPTANCE_REQUEST]",
            pr_number="6",
        )

        self.assertEqual(result["cycle"]["linked_prs"], ["6"])

    @mock.patch.object(MODULE, "collect_context_snapshot")
    @mock.patch.object(MODULE, "evaluate_acceptance_request")
    def test_run_cycle_preserves_request_and_cycle_ids_for_rework_result(
        self,
        mock_evaluate,
        mock_collect,
    ):
        mock_collect.return_value = {
            "work_item": {"record_id": "rec789", "fields": {"Title": "Pilot item"}},
            "objective": {},
            "key_result": {},
            "context_summary": "Pilot item",
        }
        mock_evaluate.return_value = {
            "decision": "REWORK",
            "protocol_read_result": "PARTIAL",
            "source_of_truth_verdict": "ambiguous",
            "reason_codes": ["RULE_ACCEPTANCE_FIELD_MISSING"],
            "recommended_next_action": "author: complete the missing fields",
        }

        result = MODULE.run_cycle(
            cycle={
                "acceptance_cycle_id": "ac-20260607-001",
                "work_item_id": "WI-123",
                "latest_acceptance_request_id": "ar-20260607-006",
                "current_phase": "context-reader",
                "cycle_status": "requested",
                "linked_prs": ["6"],
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            },
            comment_body="[验收委托 / ACCEPTANCE_REQUEST]",
            pr_number="6",
        )

        self.assertEqual(result["validation_result"]["acceptance_request_id"], "ar-20260607-006")
        self.assertEqual(result["validation_result"]["acceptance_cycle_id"], "ac-20260607-001")
        self.assertIn("Acceptance Request ID: ar-20260607-006", result["comment_body"])
        self.assertEqual(
            result["lark_summary_patch"]["fields"]["Latest Acceptance Request ID"],
            "ar-20260607-006",
        )

    @mock.patch.object(MODULE, "collect_context_snapshot")
    @mock.patch.object(MODULE, "evaluate_acceptance_request")
    def test_run_cycle_preserves_request_and_cycle_ids_for_block_result(
        self,
        mock_evaluate,
        mock_collect,
    ):
        mock_collect.return_value = {
            "work_item": {"record_id": "rec789", "fields": {"Title": "Pilot item"}},
            "objective": {},
            "key_result": {},
            "context_summary": "Pilot item",
        }
        mock_evaluate.return_value = {
            "decision": "BLOCK",
            "protocol_read_result": "FAIL",
            "source_of_truth_verdict": "invalid",
            "reason_codes": ["RULE_ACCEPTANCE_ANCHOR_MISSING"],
            "recommended_next_action": "author: post a valid ACCEPTANCE_REQUEST comment",
        }

        result = MODULE.run_cycle(
            cycle={
                "acceptance_cycle_id": "ac-20260607-001",
                "work_item_id": "WI-123",
                "latest_acceptance_request_id": "ar-20260607-006",
                "current_phase": "context-reader",
                "cycle_status": "requested",
                "linked_prs": ["6"],
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            },
            comment_body="[验收委托 / ACCEPTANCE_REQUEST]",
            pr_number="6",
        )

        self.assertEqual(result["validation_result"]["acceptance_request_id"], "ar-20260607-006")
        self.assertEqual(result["validation_result"]["acceptance_cycle_id"], "ac-20260607-001")
        self.assertIn("Acceptance Request ID: ar-20260607-006", result["comment_body"])
        self.assertEqual(
            result["lark_summary_patch"]["fields"]["Acceptance Status"], "blocked"
        )

    @mock.patch.object(MODULE, "run_cycle")
    def test_main_reads_cycle_file_and_prints_run_payload(self, mock_run_cycle):
        mock_run_cycle.return_value = {
            "cycle": {"acceptance_cycle_id": "ac-20260607-001"},
            "context_snapshot": {"context_summary": "Pilot item"},
            "validation_result": {"decision": "ACCEPTED"},
            "comment_body": "[验证结论 / VALIDATION_RESULT]",
            "lark_summary_patch": {"fields": {"Acceptance Status": "accepted"}},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cycle_path = Path(tmpdir) / "acceptance_cycle.json"
            cycle_path.write_text(
                json.dumps(
                    {
                        "acceptance_cycle_id": "ac-20260607-001",
                        "linked_prs": ["6"],
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with mock.patch.object(sys, "argv", ["run_acceptance_cycle.py", str(cycle_path)]):
                with mock.patch.dict(
                    os.environ,
                    {
                        "COMMENT_BODY": "[验收委托 / ACCEPTANCE_REQUEST]",
                        "PR_NUMBER": "6",
                    },
                    clear=False,
                ):
                    with mock.patch("sys.stdout", new=stdout):
                        MODULE.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["validation_result"]["decision"], "ACCEPTED")
        self.assertEqual(payload["lark_summary_patch"]["fields"]["Acceptance Status"], "accepted")


if __name__ == "__main__":
    unittest.main()

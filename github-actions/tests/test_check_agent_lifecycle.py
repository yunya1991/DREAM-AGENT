import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "check_agent_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("check_agent_lifecycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LifecycleCheckerTests(unittest.TestCase):
    def test_rule_catalog_and_checker_mapping_stay_in_sync(self):
        rule_ids = {rule["id"] for rule in MODULE.load_rules()}
        self.assertEqual(rule_ids, set(MODULE.build_rule_checkers(MODULE.load_rules())))

    def test_rule_catalog_keeps_shared_baseline_and_legacy_flow_metadata(self):
        catalog = json.loads(MODULE.RULES_PATH.read_text(encoding="utf-8"))
        checks_by_id = {rule["id"]: rule["check"] for rule in catalog["rules"]}

        self.assertEqual(catalog["version"], "1.1")
        self.assertEqual(checks_by_id["RULE_001_TASK_CARD_REQUIRED"], "task_card_present")
        self.assertEqual(
            checks_by_id["RULE_002_DESIGN_REVIEW_REQUIRED"],
            "design_review_present_for_legacy_flow",
        )
        self.assertEqual(
            checks_by_id["RULE_003_STARTED_REQUIRED"],
            "started_comment_present_for_legacy_flow",
        )
        self.assertEqual(checks_by_id["RULE_009_BRANCH_POLICY_ENFORCED"], "branch_policy_valid")
        self.assertEqual(
            checks_by_id["RULE_010_SHARED_FILE_DECLARATION"], "shared_files_declared"
        )

    def test_pass_when_common_baseline_and_acceptance_flow_exist(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST", "VALIDATION_RESULT"],
            "acceptance_request_present": True,
            "validation_result_present": True,
            "validation_decision": "ACCEPTED",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["reason_codes"], [])

    def test_pending_when_acceptance_request_exists_without_validation_result(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST"],
            "acceptance_request_present": True,
            "validation_result_present": False,
            "validation_decision": "",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "PENDING")
        self.assertIn("RULE_VALIDATION_RESULT_PENDING", result["reason_codes"])

    def test_block_when_validation_result_exists_but_decision_is_blocking(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST", "VALIDATION_RESULT"],
            "acceptance_request_present": True,
            "validation_result_present": True,
            "validation_decision": "REWORK",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_ACCEPTANCE_VALIDATION_BLOCKED", result["reason_codes"])

    def test_main_exits_zero_for_pending_acceptance_state(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST"],
            "acceptance_request_present": True,
            "validation_result_present": False,
            "validation_decision": "",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")

            with mock.patch("sys.argv", ["check_agent_lifecycle.py", str(payload_path)]):
                with mock.patch("sys.stdout", new=io.StringIO()):
                    with self.assertRaises(SystemExit) as cm:
                        MODULE.main()

        self.assertEqual(cm.exception.code, 0)

    def test_pending_when_acceptance_request_exists_without_validation_result_on_pilot_branch(self):
        payload = {
            "branch": "pilot/acceptance-auto-trigger-20260607",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST"],
            "acceptance_request_present": True,
            "validation_result_present": False,
            "validation_decision": "",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "PENDING")
        self.assertEqual(result["reason_codes"], ["RULE_VALIDATION_RESULT_PENDING"])

    def test_pass_when_legacy_flow_still_has_all_required_evidence(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED", "DONE"],
            "acceptance_request_present": False,
            "validation_result_present": False,
            "validation_decision": "",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "PASS")

    def test_pass_when_all_required_evidence_exists(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED", "DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["reason_codes"], [])

    def test_block_when_started_comment_is_missing(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_003_STARTED_REQUIRED", result["reason_codes"])

    def test_block_when_branch_policy_is_invalid(self):
        payload = {
            "branch": "main",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED", "DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_009_BRANCH_POLICY_ENFORCED", result["reason_codes"])

    def test_block_when_design_review_is_missing(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": False,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED", "DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_002_DESIGN_REVIEW_REQUIRED", result["reason_codes"])

    def test_block_when_done_comment_is_missing(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_008_DONE_REQUIRED", result["reason_codes"])

    def test_block_when_shared_files_are_not_declared(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": False,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED", "DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_010_SHARED_FILE_DECLARATION", result["reason_codes"])

    def test_block_when_scope_change_declared_without_updated_comment(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_change_declared": True,
            "block_declared": False,
            "comments": ["STARTED", "DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_004_SCOPE_CHANGE_MUST_UPDATE", result["reason_codes"])

    def test_block_when_block_declared_without_blocked_comment(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "owner_agent": "SOLO",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_change_declared": False,
            "block_declared": True,
            "comments": ["STARTED", "DONE"],
        }
        result = MODULE.evaluate_payload(payload)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_005_BLOCK_MUST_ANNOUNCE", result["reason_codes"])

    def test_rule_checker_mapping_is_built_from_current_rules_file(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "comments": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_rules = Path(tmpdir) / "rules.json"
            temp_rules.write_text(
                json.dumps(
                    {
                        "rules": [
                            {
                                "id": "RULE_RUNTIME_DONE_REQUIRED",
                                "severity": "block",
                                "check": "done_comment_present",
                                "checker": "check_done_comment_present",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            original_rules_path = MODULE.RULES_PATH
            MODULE.RULES_PATH = temp_rules
            try:
                result = MODULE.evaluate_payload(payload)
            finally:
                MODULE.RULES_PATH = original_rules_path

        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason_codes"], ["RULE_RUNTIME_DONE_REQUIRED"])
        self.assertEqual(result["evaluated_rule_count"], 1)


if __name__ == "__main__":
    unittest.main()

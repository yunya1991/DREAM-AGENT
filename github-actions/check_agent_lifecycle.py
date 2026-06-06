import json
import sys
from pathlib import Path


RULES_PATH = (
    Path(__file__).resolve().parents[1]
    / "SKILLS"
    / "agent-collab-supervisor"
    / "rules.json"
)

ALLOWED_BRANCH_PREFIXES = (
    "agent/",
    "milestone/",
    "design/",
    "acceptance/",
    "protocol/",
)

STANDARD_RULE_CHECKERS = {
    "check_task_card_present",
    "check_design_review_present",
    "check_started_comment_present",
    "check_scope_change_announcement",
    "check_block_announcement",
    "check_test_report_present",
    "check_non_owner_review_present",
    "check_done_comment_present",
    "check_branch_policy_valid",
    "check_shared_files_declared",
}


def load_rules():
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"rules file not found: {RULES_PATH}")
    with RULES_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)["rules"]


def branch_policy_valid(branch):
    return branch.startswith(ALLOWED_BRANCH_PREFIXES)


def payload_flag(payload, new_key, legacy_key):
    if new_key in payload:
        return bool(payload.get(new_key))
    return bool(payload.get(legacy_key))


def check_task_card_present(payload):
    return bool(payload.get("task_card_present"))


def check_design_review_present(payload):
    return bool(payload.get("design_review_present"))


def check_started_comment_present(payload):
    return "STARTED" in payload.get("comments", [])


def check_scope_change_announcement(payload):
    return (not payload_flag(payload, "scope_change_declared", "scope_changed")) or (
        "UPDATED" in payload.get("comments", [])
    )


def check_block_announcement(payload):
    return (not payload_flag(payload, "block_declared", "execution_blocked")) or (
        "BLOCKED" in payload.get("comments", [])
    )


def check_test_report_present(payload):
    return bool(payload.get("test_report_present"))


def check_non_owner_review_present(payload):
    return bool(payload.get("non_owner_review_present"))


def check_done_comment_present(payload):
    return "DONE" in payload.get("comments", [])


def check_branch_policy_valid(payload):
    return branch_policy_valid(payload.get("branch", ""))


def check_shared_files_declared(payload):
    return bool(payload.get("shared_files_declared"))


def check_acceptance_request_present(payload):
    return bool(payload.get("acceptance_request_present"))


def check_validation_result_present(payload):
    return bool(payload.get("validation_result_present"))


def check_validation_decision_not_blocked(payload):
    return payload.get("validation_decision", "").upper() not in {"", "BLOCK", "REWORK"}


CHECKERS = {
    "check_task_card_present": check_task_card_present,
    "check_design_review_present": check_design_review_present,
    "check_started_comment_present": check_started_comment_present,
    "check_scope_change_announcement": check_scope_change_announcement,
    "check_block_announcement": check_block_announcement,
    "check_test_report_present": check_test_report_present,
    "check_non_owner_review_present": check_non_owner_review_present,
    "check_done_comment_present": check_done_comment_present,
    "check_branch_policy_valid": check_branch_policy_valid,
    "check_shared_files_declared": check_shared_files_declared,
    "check_acceptance_request_present": check_acceptance_request_present,
    "check_validation_result_present": check_validation_result_present,
    "check_validation_decision_not_blocked": check_validation_decision_not_blocked,
}


def build_rule_checkers(rules):
    rule_checkers = {}
    for rule in rules:
        checker_name = rule["checker"]
        if checker_name not in CHECKERS:
            raise KeyError(f"unknown checker '{checker_name}' for rule {rule['id']}")
        rule_checkers[rule["id"]] = CHECKERS[checker_name]
    return rule_checkers


def uses_standard_lifecycle_rules(rules):
    return {rule["checker"] for rule in rules} == STANDARD_RULE_CHECKERS


def rule_id_by_checker(rules, checker_name, default):
    for rule in rules:
        if rule["checker"] == checker_name:
            return rule["id"]
    return default


def evaluate_via_rule_catalog(payload, rules):
    rule_checkers = build_rule_checkers(rules)
    reason_codes = []
    for rule in rules:
        if not rule_checkers[rule["id"]](payload):
            reason_codes.append(rule["id"])

    return {
        "decision": "PASS" if not reason_codes else "BLOCK",
        "reason_codes": reason_codes,
        "evaluated_rule_count": len(rules),
    }


def common_baseline_failures(payload, rules):
    failures = []
    if not check_task_card_present(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_task_card_present", "RULE_001_TASK_CARD_REQUIRED"
            )
        )
    if not check_shared_files_declared(payload):
        failures.append(
            rule_id_by_checker(
                rules,
                "check_shared_files_declared",
                "RULE_010_SHARED_FILE_DECLARATION",
            )
        )
    if not check_branch_policy_valid(payload):
        failures.append(
            rule_id_by_checker(
                rules,
                "check_branch_policy_valid",
                "RULE_009_BRANCH_POLICY_ENFORCED",
            )
        )
    return failures


def legacy_flow_pass(payload):
    return (
        check_started_comment_present(payload)
        and check_design_review_present(payload)
        and check_test_report_present(payload)
        and check_non_owner_review_present(payload)
        and check_done_comment_present(payload)
        and check_scope_change_announcement(payload)
        and check_block_announcement(payload)
    )


def acceptance_flow_pass(payload):
    if not check_acceptance_request_present(payload):
        return False
    return check_validation_result_present(payload) and check_validation_decision_not_blocked(
        payload
    )


def legacy_flow_failures(payload, rules):
    failures = []
    if not check_design_review_present(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_design_review_present", "RULE_002_DESIGN_REVIEW_REQUIRED"
            )
        )
    if not check_started_comment_present(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_started_comment_present", "RULE_003_STARTED_REQUIRED"
            )
        )
    if not check_scope_change_announcement(payload):
        failures.append(
            rule_id_by_checker(
                rules,
                "check_scope_change_announcement",
                "RULE_004_SCOPE_CHANGE_MUST_UPDATE",
            )
        )
    if not check_block_announcement(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_block_announcement", "RULE_005_BLOCK_MUST_ANNOUNCE"
            )
        )
    if not check_test_report_present(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_test_report_present", "RULE_006_TEST_EVIDENCE_REQUIRED"
            )
        )
    if not check_non_owner_review_present(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_non_owner_review_present", "RULE_007_REVIEW_BY_NON_OWNER"
            )
        )
    if not check_done_comment_present(payload):
        failures.append(
            rule_id_by_checker(
                rules, "check_done_comment_present", "RULE_008_DONE_REQUIRED"
            )
        )
    return failures


def evaluate_payload(payload):
    rules = load_rules()
    if not uses_standard_lifecycle_rules(rules):
        return evaluate_via_rule_catalog(payload, rules)

    reason_codes = common_baseline_failures(payload, rules)
    if reason_codes:
        return {
            "decision": "BLOCK",
            "reason_codes": reason_codes,
            "evaluated_rule_count": len(rules),
        }

    if legacy_flow_pass(payload) or acceptance_flow_pass(payload):
        return {
            "decision": "PASS",
            "reason_codes": [],
            "evaluated_rule_count": len(rules),
        }

    if check_acceptance_request_present(payload) and not check_validation_result_present(
        payload
    ):
        return {
            "decision": "BLOCK",
            "reason_codes": ["RULE_VALIDATION_RESULT_REQUIRED"],
            "evaluated_rule_count": len(rules),
        }

    if check_acceptance_request_present(payload) and not check_validation_decision_not_blocked(
        payload
    ):
        return {
            "decision": "BLOCK",
            "reason_codes": ["RULE_ACCEPTANCE_VALIDATION_BLOCKED"],
            "evaluated_rule_count": len(rules),
        }

    return {
        "decision": "BLOCK",
        "reason_codes": legacy_flow_failures(payload, rules),
        "evaluated_rule_count": len(rules),
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_agent_lifecycle.py <payload.json>")

    payload_path = Path(sys.argv[1])
    with payload_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    result = evaluate_payload(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["decision"] == "PASS" else 1)


if __name__ == "__main__":
    main()

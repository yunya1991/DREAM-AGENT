import json
import os
import sys
from pathlib import Path

from check_acceptance_request import evaluate_acceptance_request
from collect_lark_context import collect_context_snapshot
from manage_acceptance_cycle import apply_cycle_progress


def ensure_validation_result_identifiers(cycle: dict, validation_result: dict) -> dict:
    result = dict(validation_result)
    result.setdefault(
        "acceptance_request_id", cycle.get("latest_acceptance_request_id", "")
    )
    result.setdefault("acceptance_cycle_id", cycle.get("acceptance_cycle_id", ""))
    result.setdefault("work_item_id", cycle.get("work_item_id", ""))
    return result


def first_non_empty_value(data: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = data.get(key, "")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def build_context_snapshot_lines(cycle: dict, context_snapshot: dict) -> list[str]:
    lines = [
        f"- work_item_title={context_snapshot.get('context_summary', '')}",
        f"- pr_number={cycle['linked_prs'][0] if cycle.get('linked_prs') else ''}",
    ]

    objective = context_snapshot.get("objective") or {}
    objective_id = first_non_empty_value(objective, ("id",))
    objective_title = first_non_empty_value(
        objective,
        ("name", "title", "objective_title"),
    )
    if objective_id:
        lines.append(f"- objective_id={objective_id}")
    if objective_title:
        lines.append(f"- objective_title={objective_title}")

    key_result = context_snapshot.get("key_result") or {}
    key_result_id = first_non_empty_value(key_result, ("id",))
    key_result_title = first_non_empty_value(
        key_result,
        ("name", "title", "key_result_title"),
    )
    if key_result_id:
        lines.append(f"- key_result_id={key_result_id}")
    if key_result_title:
        lines.append(f"- key_result_title={key_result_title}")

    return lines


def build_validation_result_comment(
    cycle: dict,
    validation_result: dict,
    context_snapshot: dict,
) -> str:
    hard_gate = "BLOCK" if validation_result["decision"] == "BLOCK" else "PASS"
    conclusion_map = {
        "ACCEPTED": "accepted",
        "REWORK": "rework",
        "BLOCK": "blocked",
    }
    lines = [
        "[验证结论 / VALIDATION_RESULT]",
        "",
        "Validator: result-synthesizer",
        "Validation Mode: acceptance",
        f"Acceptance Request ID: {validation_result['acceptance_request_id']}",
        f"Acceptance Cycle ID: {cycle['acceptance_cycle_id']}",
        f"Hard Gate Result: {hard_gate}",
        "Score: 90",
        f"Decision: {validation_result['decision']}",
        f"Protocol Read Result: {validation_result['protocol_read_result']}",
        f"Source of Truth Verdict: {validation_result['source_of_truth_verdict']}",
        "Reason Codes:",
        f"- {','.join(validation_result['reason_codes'])}",
        "Must-Fix Items:",
        "- none"
        if validation_result["decision"] == "ACCEPTED"
        else "- complete the protocol gaps before rerun",
        f"Next Step Recommendation: {validation_result['recommended_next_action']}",
        f"Acceptance Conclusion: {conclusion_map[validation_result['decision']]}",
        "Reward Multiplier: 1.0",
        "Ledger Update: none",
        "Governance Handoff: pending",
        "",
        "Context Snapshot:",
    ]
    lines.extend(build_context_snapshot_lines(cycle, context_snapshot))
    return "\n".join(lines) + "\n"


def build_lark_summary_patch(cycle: dict, validation_result: dict) -> dict:
    status_map = {
        "ACCEPTED": "accepted",
        "REWORK": "rework",
        "BLOCK": "blocked",
    }
    return {
        "fields": {
            "Acceptance Cycle ID": cycle["acceptance_cycle_id"],
            "Acceptance Status": status_map[validation_result["decision"]],
            "Latest Acceptance Request ID": validation_result["acceptance_request_id"],
            "Latest Validation Decision": validation_result["decision"],
        }
    }


def run_cycle(cycle: dict, comment_body: str, pr_number: str) -> dict:
    linked_prs = cycle.setdefault("linked_prs", [])
    if pr_number not in linked_prs:
        linked_prs.append(pr_number)

    context_snapshot = collect_context_snapshot(cycle)
    cycle = apply_cycle_progress(
        cycle,
        phase="context-reader",
        cycle_status="context_collected",
        validation_result_id="",
        agent_output=context_snapshot,
    )

    protocol_result = evaluate_acceptance_request(comment_body)
    cycle = apply_cycle_progress(
        cycle,
        phase="protocol-checker",
        cycle_status="protocol_checked",
        validation_result_id="",
        agent_output=protocol_result,
    )

    validation_result = ensure_validation_result_identifiers(cycle, protocol_result)
    cycle = apply_cycle_progress(
        cycle,
        phase="acceptance-validator",
        cycle_status="validation_running",
        validation_result_id="",
        agent_output=validation_result,
    )

    comment_body = build_validation_result_comment(
        cycle, validation_result, context_snapshot
    )
    cycle = apply_cycle_progress(
        cycle,
        phase="result-synthesizer",
        cycle_status="validated",
        validation_result_id=f"vr-{cycle['acceptance_cycle_id']}",
        agent_output={"decision": validation_result["decision"], "comment_body": comment_body},
    )

    return {
        "cycle": cycle,
        "context_snapshot": context_snapshot,
        "validation_result": validation_result,
        "comment_body": comment_body,
        "lark_summary_patch": build_lark_summary_patch(cycle, validation_result),
    }


def main() -> None:
    cycle_path = Path(sys.argv[1])
    cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
    result = run_cycle(
        cycle=cycle,
        comment_body=os.environ.get("COMMENT_BODY", ""),
        pr_number=os.environ.get("PR_NUMBER", ""),
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

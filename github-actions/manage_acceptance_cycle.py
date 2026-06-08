import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from check_acceptance_request import evaluate_acceptance_request


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_cycle_record(
    acceptance_cycle_id: str,
    work_item_id: str,
    pr_number: str,
    acceptance_request_id: str,
    lark_base_url: str,
    lark_table_id: str,
    lark_record_id: str,
) -> dict:
    return {
        "acceptance_cycle_id": acceptance_cycle_id,
        "work_item_id": work_item_id,
        "cycle_status": "requested",
        "creation_mode": "manual",
        "linked_prs": [pr_number],
        "latest_acceptance_request_id": acceptance_request_id,
        "latest_validation_result_id": "",
        "current_phase": "context-reader",
        "lark_context_locator": {
            "base_url": lark_base_url,
            "table_id": lark_table_id,
            "record_id": lark_record_id,
        },
        "agent_outputs": {
            "context-reader": {},
            "protocol-checker": {},
            "acceptance-validator": {},
            "result-synthesizer": {},
        },
        "artifacts": {
            "context_snapshot_file": "",
            "validation_result_comment_file": "",
        },
    }


def apply_cycle_progress(
    cycle: dict,
    phase: str,
    cycle_status: str,
    validation_result_id: str,
    agent_output: dict,
) -> dict:
    cycle["current_phase"] = phase
    cycle["cycle_status"] = cycle_status
    if validation_result_id:
        cycle["latest_validation_result_id"] = validation_result_id
    cycle.setdefault("agent_outputs", {})[phase] = dict(agent_output)
    return cycle


def create_manual_cycle(
    root: Path,
    acceptance_cycle_id: str,
    work_item_id: str,
    pr_number: str,
    acceptance_request_id: str,
    lark_base_url: str,
    lark_table_id: str,
    lark_record_id: str,
) -> dict:
    ledger_dir = root / "ledger" / "acceptance_cycles"
    index_path = ledger_dir / "index.json"
    record = build_cycle_record(
        acceptance_cycle_id,
        work_item_id,
        pr_number,
        acceptance_request_id,
        lark_base_url,
        lark_table_id,
        lark_record_id,
    )
    (ledger_dir / f"{acceptance_cycle_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["generated_at"] = utc_now()
    index_payload["open_cycles"].append(acceptance_cycle_id)
    index_payload["cycles"].append(
        {
            "acceptance_cycle_id": acceptance_cycle_id,
            "work_item_id": work_item_id,
            "cycle_status": "requested",
            "linked_prs": [pr_number],
        }
    )
    index_path.write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return record


def load_or_create_cycle(
    root: Path,
    acceptance_cycle_id: str,
    work_item_id: str,
    pr_number: str,
    acceptance_request_id: str,
    lark_base_url: str,
    lark_table_id: str,
    lark_record_id: str,
) -> dict:
    record_path = root / "ledger" / "acceptance_cycles" / f"{acceptance_cycle_id}.json"
    if record_path.exists():
        return json.loads(record_path.read_text(encoding="utf-8"))
    return create_manual_cycle(
        root=root,
        acceptance_cycle_id=acceptance_cycle_id,
        work_item_id=work_item_id,
        pr_number=pr_number,
        acceptance_request_id=acceptance_request_id,
        lark_base_url=lark_base_url,
        lark_table_id=lark_table_id,
        lark_record_id=lark_record_id,
    )


def resolve_cycle_metadata(comment_body: str) -> dict:
    result = evaluate_acceptance_request(comment_body)
    if result["decision"] != "ACCEPTED":
        raise ValueError(
            "ACCEPTANCE_REQUEST must be accepted before creating an acceptance cycle"
        )
    return result


def main() -> None:
    root = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
    comment_body = os.environ.get("COMMENT_BODY", "")
    pr_number = os.environ.get("PR_NUMBER", "")
    metadata = resolve_cycle_metadata(comment_body)
    cycle = load_or_create_cycle(
        root=root,
        acceptance_cycle_id=metadata["acceptance_cycle_id"],
        work_item_id=metadata["work_item_id"],
        pr_number=pr_number,
        acceptance_request_id=metadata["acceptance_request_id"],
        lark_base_url=metadata["lark_base_url"],
        lark_table_id=metadata["lark_table_id"],
        lark_record_id=metadata["lark_record_id"],
    )
    json.dump(cycle, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

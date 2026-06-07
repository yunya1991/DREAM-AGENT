import json
import sys
from pathlib import Path

from lark_cli import ensure_lark_auth, run_lark_json


def extract_base_token(base_url: str) -> str:
    return base_url.split("/base/", 1)[1].split("?", 1)[0]


def get_base_record(base_token: str, table_id: str, record_id: str) -> dict:
    payload = run_lark_json(
        [
            "base",
            "+record-get",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--record-id",
            record_id,
        ]
    )
    data = payload["data"]
    if "records" in data:
        return data["records"][0]

    rows = data.get("data", [])
    field_names = data.get("fields", [])
    record_ids = data.get("record_id_list", [])
    record_index = record_ids.index(record_id) if record_id in record_ids else 0
    row = rows[record_index] if record_index < len(rows) else []
    return {
        "record_id": record_ids[record_index] if record_index < len(record_ids) else record_id,
        "fields": dict(zip(field_names, row)),
    }


def get_objective(objective_id: str) -> dict:
    payload = run_lark_json(
        ["okr", "objectives", "get", "--params", f'{{"objective_id":"{objective_id}"}}']
    )
    return payload["data"]["objective"]


def get_key_result(key_result_id: str) -> dict:
    payload = run_lark_json(
        [
            "okr",
            "key_results",
            "get",
            "--params",
            f'{{"key_result_id":"{key_result_id}"}}',
        ]
    )
    return payload["data"]["key_result"]


def collect_context_snapshot(cycle: dict) -> dict:
    locator = cycle["lark_context_locator"]
    ensure_lark_auth(identity="user")
    base_token = extract_base_token(locator["base_url"])
    record = get_base_record(base_token, locator["table_id"], locator["record_id"])
    fields = record.get("fields", {})
    objective_id = fields.get("Objective ID", "")
    key_result_id = fields.get("KR ID", "")
    objective = get_objective(objective_id) if objective_id else {}
    key_result = get_key_result(key_result_id) if key_result_id else {}
    return {
        "work_item": {
            "record_id": record["record_id"],
            "fields": fields,
        },
        "objective": objective,
        "key_result": key_result,
        "context_summary": fields.get("Title", ""),
    }


def main() -> None:
    cycle_path = Path(sys.argv[1])
    cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
    snapshot = collect_context_snapshot(cycle)
    json.dump(snapshot, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

import json
import sys


WRITEBACK_ORDER = [
    "intake_normalization",
    "asset_target_resolution",
    "validation_snapshot",
    "knowledge_asset_writeback",
    "index_alignment_check",
]


def materialize_knowledge_asset(preview):
    status = "confirmed"
    risk_flags = preview.get("risk_flags", [])
    check_report = preview.get("check_report", {})
    if "unknown_asset_type" in risk_flags or "empty_title" in risk_flags:
        status = "hard_block"
    elif check_report.get("gap_flags"):
        status = "soft_block"
    elif check_report.get("stale_flags"):
        status = "degraded_success"

    target_path = preview["asset_target_candidate"].get("target_path", "")

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "asset_target": preview["asset_target_candidate"],
        "validation_report": preview["validation_report"],
        "check_report": check_report,
        "knowledge_update": {
            "asset_type": preview["intake_summary"].get("asset_type", ""),
            "title": preview["intake_summary"].get("title", ""),
            "summary": f"status={status}",
            "evidence_refs": [target_path] if target_path else [],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"knowledge ops execution {status}",
            "next_action": "review knowledge verification result",
            "evidence_refs": [target_path] if target_path else [],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_knowledge_asset(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")

import json
import sys


def verify_knowledge_asset(asset_target, validation_report, check_report, existing_state):
    if not asset_target.get("target_path"):
        status = "hard_block"
    elif check_report.get("gap_flags") or not existing_state.get("index_aligned", False):
        status = "soft_block"
    elif check_report.get("stale_flags"):
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "target_path": asset_target.get("target_path", ""),
        "index_aligned": existing_state.get("index_aligned", False),
        "target_exists": existing_state.get("target_exists", False),
        "has_drift": bool(check_report.get("drift_flags")),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_knowledge_asset(
            payload["asset_target"],
            payload["validation_report"],
            payload["check_report"],
            payload["existing_state"],
        ),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")

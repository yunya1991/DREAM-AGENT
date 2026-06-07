import json
import sys


VALID_FEISHU_ASSET_MODES = {
    "full-sync",
    "degraded-with-backfill",
    "blocked-by-feishu-asset",
}


def evaluate_payload(payload):
    reason_codes = []
    recommended_next_action = ""

    if not payload.get("unit_id"):
        reason_codes.append("RULE_UNIT_ID_REQUIRED")
    if not payload.get("track"):
        reason_codes.append("RULE_TRACK_REQUIRED")
    if not payload.get("acceptance_mode"):
        reason_codes.append("RULE_ACCEPTANCE_MODE_REQUIRED")
    if not payload.get("rollback_level"):
        reason_codes.append("RULE_ROLLBACK_STRATEGY_REQUIRED")
    if payload.get("feishu_asset_mode") not in VALID_FEISHU_ASSET_MODES:
        reason_codes.append("RULE_INVALID_FEISHU_ASSET_MODE")

    if reason_codes:
        recommended_next_action = "governance: complete hybrid unit dispatch fields"

    return {
        "decision": "PASS" if not reason_codes else "BLOCK",
        "reason_codes": reason_codes,
        "recommended_next_action": recommended_next_action,
    }


if __name__ == "__main__":
    json.dump(evaluate_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)

import json
import sys


def evaluate_payload(payload):
    implementation_status = payload.get("implementation_status", "")
    platform_status = payload.get("platform_status", "")
    governance_status = payload.get("governance_status", "")

    reason_codes = []
    release_decision = "hold"

    if platform_status != "checks_green" and governance_status in {"ready", "released"}:
        reason_codes.append("RULE_GOVERNANCE_REQUIRES_GREEN_CHECKS")

    if platform_status == "checks_green" and implementation_status == "tested":
        release_decision = "ready_for_release"
    elif platform_status in {"checks_pending", "checks_failing", "workflow_failed"}:
        release_decision = "hold"

    return {
        "decision": "PASS" if not reason_codes else "BLOCK",
        "reason_codes": reason_codes,
        "release_decision": release_decision,
    }


if __name__ == "__main__":
    json.dump(evaluate_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)

import json
import sys
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_binding_payload(goal, objective):
    kr_summary = "；".join(objective.get("krs", []))
    decision_summary = (
        f"objective_bound:{objective['objective_id']}"
        + (f"；{kr_summary}" if kr_summary else "")
    )
    return {
        "goal_id": goal["goal_id"],
        "目标名称": goal["goal_name"],
        "OKR对齐": "已对齐",
        "okr_objective_id": objective["objective_id"],
        "okr_objective_title": objective["objective_title"],
        "okr_owner": objective["objective_owner"],
        "okr_sync_status": "bound",
        "okr_last_sync_at": now_iso(),
        "最近决策摘要": decision_summary,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_binding_payload(payload["goal"], payload["objective"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")

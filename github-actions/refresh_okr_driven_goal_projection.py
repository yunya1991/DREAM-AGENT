import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_goal_progress_record as goal_progress_record


def refresh_projection(goal, tasks):
    enriched_goal = dict(goal)
    enriched_goal.setdefault("current_phase", "hub-trading-connectivity")
    enriched_goal.setdefault(
        "next_milestone", "打通 Hub 直连 Trading 并完成三页面实时联动验证"
    )
    enriched_goal.setdefault(
        "next_action", "由开发代理认领任务并实现 Hub 侧 /api/trading/* 直连桥接"
    )
    return goal_progress_record.build_goal_record(enriched_goal, tasks)


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        refresh_projection(payload["goal"], payload["tasks"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")

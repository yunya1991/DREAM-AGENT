import json
import sys


def verify_bitable_projection(task_records, progress_records, goal_projection, view_validation):
    if not task_records or not progress_records or not goal_projection:
        status = "blocked"
    elif {item["task_id"] for item in task_records} != {
        item["task_ref"] for item in progress_records
    }:
        status = "soft_block"
    elif not view_validation:
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "task_count": len(task_records),
        "progress_count": len(progress_records),
        "goal_projection_count": len(goal_projection),
        "view_validation_count": len(view_validation),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_bitable_projection(
            payload["task_records"],
            payload["progress_records"],
            payload["goal_projection"],
            payload["view_validation"],
        ),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")

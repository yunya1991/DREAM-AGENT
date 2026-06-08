import json
import sys


def materialize_execution(preview):
    objective = preview["objective_candidates"][0]
    goal = preview["goal_record_candidates"][0]
    kr_titles = [item["title"] for item in preview["kr_candidates"]]

    return {
        "execution_mode": "preview_then_confirm",
        "okr": {
            "source_of_truth": "feishu_okr",
            "objective_title": objective["title"],
            "objective_owner": objective["owner"],
            "krs": kr_titles,
        },
        "base": {
            "projection_only": True,
            "goal_id": goal["goal_id"],
            "goal_name": goal["goal_name"],
            "anchor_fields": [
                "OKR对齐",
                "okr_objective_id",
                "okr_objective_title",
                "okr_owner",
                "okr_sync_status",
                "okr_last_sync_at",
            ],
        },
        "tasks": {"items": preview["task_candidates"]},
        "workflow": {"items": preview["workflow_candidates"]},
        "projection": {
            "refresh_fields": [
                "OKR对齐",
                "最近决策摘要",
                "workflow_signal",
                "当前状态",
                "当前阻塞",
                "风险等级",
                "下一步动作",
            ]
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")

import json
import re
import sys


OBJECTIVE_RE = re.compile(r"Objective[：:]\s*(.+)")
KR_RE = re.compile(r"KR\d+[：:]\s*(.+)")
GOAL_ID_RE = re.compile(r"goal_id\s*=\s*([A-Za-z0-9\-_]+)")
GOAL_NAME_RE = re.compile(r"目标名称\s*=\s*(.+)")


def _extract_objective(spec_text):
    match = OBJECTIVE_RE.search(spec_text)
    return match.group(1).strip() if match else ""


def _extract_krs(spec_text):
    return [match.group(1).strip() for match in KR_RE.finditer(spec_text)]


def _extract_goal(spec_text):
    goal_id_match = GOAL_ID_RE.search(spec_text)
    goal_name_match = GOAL_NAME_RE.search(spec_text)
    goal_id = goal_id_match.group(1) if goal_id_match else "goal-missing-id"
    goal_name = goal_name_match.group(1).strip() if goal_name_match else "未命名目标"
    return {
        "goal_id": str(goal_id),
        "goal_name": goal_name,
        "goal_owner": "governance-agent",
        "goal_status": "blocked",
        "risk_level": "high",
        "blocker": "",
        "next_action": "",
        "okr_anchor_ref": str(goal_id),
    }


def _extract_task_candidates(plan_text, goal_id, kr_titles):
    tasks = []
    if "Task 3" in plan_text:
        tasks.append(
            {
                "task_id": "task-create-real-okr",
                "title": "创建真实 Objective 和 4 个 KR",
                "goal_ref": str(goal_id),
                "kr_ref": kr_titles[0] if kr_titles else "",
                "owner": "governance-agent",
                "status": "planned",
                "deliverable": "real objective and kr ids",
            }
        )
    if "Task 4" in plan_text:
        tasks.append(
            {
                "task_id": "task-bind-base-record",
                "title": "回写目标推进表的 OKR 锚点字段",
                "goal_ref": str(goal_id),
                "kr_ref": "",
                "owner": "governance-agent",
                "status": "planned",
                "deliverable": "base anchor writeback",
            }
        )
    return tasks


def _extract_workflow_candidates(plan_text, goal_id):
    if "boss view" not in plan_text.lower() and "老板视图" not in plan_text:
        return []
    return [
        {
            "name": "OKR对齐缺失提醒",
            "trigger_kind": "record_change",
            "conditions": ["当前状态=推进中", "OKR对齐!=已对齐"],
            "receivers": ["OKR负责人"],
            "expected_signal": "missing_okr_alignment",
            "goal_ref": str(goal_id),
        }
    ]


def build_preview(spec_text, plan_text):
    objective_title = _extract_objective(spec_text)
    kr_titles = _extract_krs(spec_text)
    goal = _extract_goal(spec_text)
    tasks = _extract_task_candidates(plan_text, goal["goal_id"], kr_titles)
    workflows = _extract_workflow_candidates(plan_text, goal["goal_id"])

    risk_flags = []
    if not tasks:
        risk_flags.append("task_layer_incomplete")
    if not workflows:
        risk_flags.append("workflow_layer_incomplete")

    return {
        "objective_candidates": [
            {
                "title": objective_title,
                "owner": "governance-agent",
                "period_hint": "current",
                "source_spec_refs": ["spec:推荐建模方案"],
                "source_plan_refs": ["plan:Task 3"],
            }
        ],
        "kr_candidates": [
            {
                "title": title,
                "objective_ref": objective_title,
                "acceptance_signal": "result_defined",
                "source_refs": ["spec:KR"],
            }
            for title in kr_titles
        ],
        "goal_record_candidates": [goal],
        "task_candidates": tasks,
        "workflow_candidates": workflows,
        "upsert_plan": ["OKR", "Base", "Task", "workflow", "projection"],
        "risk_flags": risk_flags,
        "requires_confirmation": True,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_preview(payload["spec_text"], payload["plan_text"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")

import json
import sys


def build_feishu_record(payload):
    return {
        "任务ID": payload.get("task_id", ""),
        "任务名称": payload.get("task_name", ""),
        "目标ID": payload.get("goal_id", ""),
        "仓库": payload.get("repo", ""),
        "分支": payload.get("branch", ""),
        "PR号": payload.get("pr_number", ""),
        "Workflow运行ID": payload.get("workflow_run_id", ""),
        "实现状态": payload.get("implementation_status", ""),
        "平台状态": payload.get("platform_status", ""),
        "治理状态": payload.get("governance_status", ""),
        "自动化状态": payload.get("automation_status", ""),
        "风险等级": payload.get("risk_level", "low"),
        "审批状态": payload.get("approval_status", "not_required"),
        "审批决策ID": payload.get("approval_decision_id", ""),
        "审批截止时间": payload.get("approval_due_at", ""),
        "决策摘要": payload.get("decision_summary", ""),
        "最近评论锚点": payload.get("last_comment_anchor", ""),
        "最近提交": payload.get("last_commit", ""),
        "当前阻塞": payload.get("blocker", ""),
        "下一步建议": payload.get("next_action", ""),
        "远程动作": payload.get("remote_action", "none"),
        "远程动作结果": payload.get("remote_action_result", ""),
    }


if __name__ == "__main__":
    json.dump(build_feishu_record(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)

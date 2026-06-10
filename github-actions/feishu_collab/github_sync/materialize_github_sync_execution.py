import json
import sys


WRITEBACK_ORDER = [
    "event_coverage_check",
    "task_table_writeback",
    "goal_table_writeback",
    "monitor_table_writeback",
    "verification_snapshot",
]


def render_protocol_comment(header, preview, include_execution):
    protocol_checks = preview.get("protocol_checks", {})
    preflight = protocol_checks.get("preflight_checks", [])
    post_updates = protocol_checks.get("post_update_actions", [])
    event_summary = preview.get("event_summary", {})
    lines = [
        header,
        "",
        f"Agent: {preview.get('event_summary', {}).get('repo', 'automation-executor')}",
        "前置检查:",
    ]
    lines.extend(f"- {item}" for item in preflight)
    if include_execution:
        lines.extend(
            [
                "",
                "执行内容:",
                f"- 同步 {event_summary.get('repo', '')} #{event_summary.get('number', '')} / {event_summary.get('action', '')}",
                "",
                "Test: github-sync-preview",
                f"Result: {preview.get('event_coverage_hit', {}).get('fallback_policy', 'confirmed')}",
            ]
        )
    lines.extend(["", "后置更新:"])
    lines.extend(f"- {item}" for item in post_updates)
    return "\n".join(lines).strip()


def materialize_github_sync_execution(preview):
    status = "confirmed"
    if "event_coverage_gap" in preview.get("risk_flags", []):
        status = "soft_block"
    elif not preview.get("field_updates", {}).get("最近评论锚点"):
        status = "degraded_success"

    evidence_refs = [
        preview["event_summary"].get("repo", ""),
        preview["event_summary"].get("number", ""),
    ]

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "collab_state": {"fields": preview["field_updates"]},
        "comment_templates": {
            "started": render_protocol_comment("[协作开工声明 / STARTED]", preview, False),
            "summary": render_protocol_comment("[单次总结 / SUMMARY]", preview, True),
        },
        "event_summary": preview["event_summary"],
        "verification_seed": {
            "coverage_hit": preview["event_coverage_hit"],
            "risk_flags": preview["risk_flags"],
        },
        "knowledge_update": {
            "asset_type": "delivery",
            "title": "github-sync-writeback-result",
            "summary": f"status={status}",
            "evidence_refs": [item for item in evidence_refs if item],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"github sync execution {status}",
            "next_action": "review verification result",
            "evidence_refs": [item for item in evidence_refs if item],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_github_sync_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_okr_driven_preview import build_preview as build_okr_preview
from materialize_okr_driven_execution import materialize_execution as materialize_okr_execution
from feishu_collab.approval.build_approval_preview import build_approval_preview
from feishu_collab.approval.materialize_approval_execution import materialize_approval_execution
from feishu_collab.approval.verify_approval_projection import verify_approval_projection
from feishu_collab.bitable.build_bitable_preview import build_bitable_preview
from feishu_collab.bitable.materialize_bitable_execution import materialize_bitable_execution
from feishu_collab.bitable.verify_bitable_projection import verify_bitable_projection
from feishu_collab.github_sync.build_github_sync_preview import build_github_sync_preview
from feishu_collab.github_sync.materialize_github_sync_execution import materialize_github_sync_execution
from feishu_collab.github_sync.verify_github_sync_projection import verify_github_sync_projection
from feishu_collab.knowledge_ops.check_knowledge_assets import check_knowledge_assets
from feishu_collab.knowledge_ops.intake import normalize_knowledge_intake
from feishu_collab.knowledge_ops.materialize_knowledge_asset import materialize_knowledge_asset
from feishu_collab.knowledge_ops.pathing import resolve_knowledge_target
from feishu_collab.knowledge_ops.validate_knowledge_asset import validate_knowledge_asset
from feishu_collab.knowledge_ops.verify_knowledge_asset import verify_knowledge_asset
from feishu_collab.shared.status_adapter import normalize_skill_result


def _append_step(step_results, breakpoints, skill_name, raw_status, risk_flags, raw_result, verification):
    normalized = normalize_skill_result(
        skill_name=skill_name,
        raw_status=raw_status,
        risk_flags=risk_flags,
        verification=verification,
    )
    step = {
        "skill_name": skill_name,
        "raw_result": raw_result,
        "verification": verification,
        "normalized": normalized,
    }
    step_results.append(step)
    if normalized["system_status"] in {"warn", "fail", "blocked"}:
        breakpoints.append(
            {
                "skill_name": skill_name,
                "system_status": normalized["system_status"],
                "breakpoint_type": normalized["breakpoint_type"],
                "recovery_hint": normalized["recovery_hint"],
            }
        )
    return normalized


def run_rehearsal_chain(payload):
    inputs = payload["inputs"]
    step_results = []
    breakpoints = []

    okr_preview = build_okr_preview(inputs["okr"]["spec_text"], inputs["okr"]["plan_text"])
    okr_execution = materialize_okr_execution(okr_preview)
    okr_verification = {"status": "confirmed", "task_count": len(okr_preview["task_candidates"])}
    normalized = _append_step(
        step_results,
        breakpoints,
        "okr-driven",
        "confirmed",
        okr_preview.get("risk_flags", []),
        {"preview": okr_preview, "execution": okr_execution},
        okr_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    bitable_preview = build_bitable_preview(okr_preview, inputs["bitable"]["base_context"])
    bitable_execution = materialize_bitable_execution(bitable_preview)
    bitable_verification = verify_bitable_projection(
        bitable_preview["task_record_candidates"],
        bitable_preview["progress_record_candidates"],
        bitable_preview["goal_projection_candidates"],
        bitable_preview["view_projection_candidates"],
    )
    normalized = _append_step(
        step_results,
        breakpoints,
        "bitable",
        bitable_execution["status"],
        bitable_preview.get("drift_flags", []),
        {"preview": bitable_preview, "execution": bitable_execution},
        bitable_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    collab_context = dict(inputs["github_sync"]["collab_context"])
    collab_context["goal_id"] = bitable_preview["goal_projection_candidates"][0]["goal_id"]
    collab_context["task_id"] = bitable_preview["task_record_candidates"][0]["task_id"]
    collab_context["task_name"] = bitable_preview["task_record_candidates"][0]["title"]
    github_preview = build_github_sync_preview(inputs["github_sync"]["event_payload"], collab_context)
    github_execution = materialize_github_sync_execution(github_preview)
    github_verification = verify_github_sync_projection(
        github_execution["collab_state"]["fields"],
        github_execution["verification_seed"]["coverage_hit"],
        github_execution["verification_seed"]["risk_flags"],
        github_execution["collab_state"]["fields"].get("最近评论锚点", ""),
        {"status": github_execution["collab_state"]["fields"].get("自动化状态", "")},
    )
    normalized = _append_step(
        step_results,
        breakpoints,
        "github-sync",
        github_execution["status"],
        github_preview.get("risk_flags", []),
        {"preview": github_preview, "execution": github_execution},
        github_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    risk_context = dict(inputs["approval"]["risk_context"])
    risk_context["task_id"] = collab_context["task_id"]
    risk_context["goal_id"] = collab_context["goal_id"]
    approval_context = dict(inputs["approval"]["approval_context"])
    approval_context["target_object_id"] = collab_context["task_id"]
    approval_context["instance_external_id"] = collab_context["task_id"]
    approval_preview = build_approval_preview(risk_context, approval_context)
    approval_execution = materialize_approval_execution(approval_preview)
    approval_verification = verify_approval_projection(
        approval_execution["status_projection"],
        approval_execution["timeout_policy"],
        {
            "instance_code": approval_execution["approval_request"].get("instance_external_id", ""),
            "decision_summary": approval_execution["status_projection"].get("decision_summary", ""),
        },
        approval_preview["risk_flags"],
    )
    normalized = _append_step(
        step_results,
        breakpoints,
        "approval",
        approval_execution["status"],
        approval_preview.get("risk_flags", []),
        {"preview": approval_preview, "execution": approval_execution},
        approval_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    handoff_context = dict(inputs["knowledge_ops"]["handoff_context"])
    handoff_context["source_skill"] = "feishu-collab-approval"
    handoff_context["handoff_summary"] = approval_execution["handoff"]["summary"]
    handoff_context["target_object_id"] = collab_context["task_id"]
    handoff_context["goal_id"] = collab_context["goal_id"]
    knowledge_intake = normalize_knowledge_intake(approval_execution["knowledge_update"], handoff_context)
    validation_report = validate_knowledge_asset(knowledge_intake)
    asset_target = {
        "target_path": resolve_knowledge_target(knowledge_intake["asset_type"], knowledge_intake["title"]),
        "template_type": "runbook",
        "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
        "allow_overwrite": False,
    }
    check_report = check_knowledge_assets(
        intake=knowledge_intake,
        validation_report=validation_report,
        existing_state={"index_contains_target": True, "stale_hint": False},
    )
    knowledge_preview = {
        "intake_summary": knowledge_intake,
        "asset_target_candidate": asset_target,
        "validation_report": validation_report,
        "check_report": check_report,
        "risk_flags": validation_report["risk_flags"],
        "requires_confirmation": True,
    }
    knowledge_execution = materialize_knowledge_asset(knowledge_preview)
    knowledge_verification = verify_knowledge_asset(
        knowledge_execution["asset_target"],
        knowledge_execution["validation_report"],
        knowledge_execution["check_report"],
        {"target_exists": True, "index_aligned": True},
    )
    _append_step(
        step_results,
        breakpoints,
        "knowledge-ops",
        knowledge_execution["status"],
        knowledge_preview["risk_flags"],
        {"preview": knowledge_preview, "execution": knowledge_execution},
        knowledge_verification,
    )

    return {"step_results": step_results, "breakpoints": breakpoints}

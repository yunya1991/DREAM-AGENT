STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2, "blocked": 3}


def _system_status(step_results):
    if not step_results:
        return "blocked"
    return max(
        (step["normalized"]["system_status"] for step in step_results),
        key=lambda value: STATUS_ORDER[value],
    )


def build_rehearsal_report(scenario_manifest, step_results, breakpoints):
    system_status = _system_status(step_results)
    final_execution = step_results[-1]["raw_result"]["execution"] if step_results else {}
    return {
        "scenario_manifest": scenario_manifest,
        "step_results": step_results,
        "breakpoints": breakpoints,
        "system_status": system_status,
        "verification_summary": {
            "step_count": len(step_results),
            "breakpoint_count": len(breakpoints),
            "highest_status": system_status,
        },
        "handoff": {
            "type": "stage_handoff",
            "status": system_status,
            "summary": f"five skill rehearsal {system_status}",
            "next_action": "review breakpoints and rerun if needed",
            "evidence_refs": [item["skill_name"] for item in step_results],
        },
        "knowledge_update": final_execution.get(
            "knowledge_update",
            {
                "asset_type": "delivery",
                "title": "five-skill-rehearsal-result",
                "summary": f"status={system_status}",
                "evidence_refs": [item["skill_name"] for item in step_results],
            },
        ),
    }

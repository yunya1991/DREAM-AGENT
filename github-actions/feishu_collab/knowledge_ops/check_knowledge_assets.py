def check_knowledge_assets(intake, validation_report, existing_state):
    drift_flags = []
    gap_flags = []
    stale_flags = []
    severity = "none"
    repair_suggestions = []

    if not validation_report.get("title_valid") or not validation_report.get("asset_type_valid"):
        drift_flags.append("validation_drift")
        severity = "high"
        repair_suggestions.append("fix title or asset type")

    if not existing_state.get("index_contains_target", False):
        gap_flags.append("index_alignment_gap")
        if severity == "none":
            severity = "medium"
        repair_suggestions.append("add target to index")

    if existing_state.get("stale_hint", False):
        stale_flags.append("stale_source_hint")
        if severity == "none":
            severity = "medium"
        repair_suggestions.append("refresh stale asset metadata")

    return {
        "drift_flags": drift_flags,
        "gap_flags": gap_flags,
        "stale_flags": stale_flags,
        "severity": severity,
        "repair_suggestions": repair_suggestions,
    }

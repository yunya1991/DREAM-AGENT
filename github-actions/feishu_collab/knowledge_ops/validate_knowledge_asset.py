def validate_knowledge_asset(intake):
    asset_type = intake.get("asset_type", "")
    title = intake.get("title", "")
    evidence_refs = intake.get("evidence_refs", [])
    risk_flags = []

    title_valid = bool(title.strip())
    if not title_valid:
        risk_flags.append("empty_title")

    asset_type_valid = asset_type in {"operations", "delivery", "architecture", "policy"}
    if not asset_type_valid:
        risk_flags.append("unknown_asset_type")

    evidence_valid = bool(evidence_refs)
    if not evidence_valid:
        risk_flags.append("missing_evidence_refs")

    template_type = "runbook" if asset_type == "operations" else "handoff"
    if asset_type in {"architecture", "policy"}:
        template_type = "governance"

    return {
        "title_valid": title_valid,
        "asset_type_valid": asset_type_valid,
        "evidence_valid": evidence_valid,
        "template_type": template_type,
        "risk_flags": risk_flags,
    }

def normalize_knowledge_intake(knowledge_update, handoff_context):
    return {
        "asset_type": knowledge_update.get("asset_type", ""),
        "title": knowledge_update.get("title", ""),
        "summary": knowledge_update.get("summary", ""),
        "evidence_refs": knowledge_update.get("evidence_refs", []),
        "source_skill": handoff_context.get("source_skill", ""),
        "handoff_summary": handoff_context.get("handoff_summary", ""),
        "target_object_id": handoff_context.get("target_object_id", ""),
        "goal_id": handoff_context.get("goal_id", ""),
    }

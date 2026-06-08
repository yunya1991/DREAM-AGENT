import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module(name, relative_path):
    path = HERE / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_module(
    "build_real_knowledge_payload",
    "feishu_collab/knowledge_ops/build_real_knowledge_payload.py",
)
MATERIALIZE = load_module(
    "materialize_real_knowledge_assets",
    "feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py",
)
UPDATE = load_module(
    "update_knowledge_indexes",
    "feishu_collab/knowledge_ops/update_knowledge_indexes.py",
)


def _entry_purpose(title, document_type):
    if document_type == "runbook":
        return f"Track {title} recovery and verification"
    return f"Hand off {title} follow-up work"


def _collect_evidence_refs(runbook_result, handoff_result):
    evidence_refs = []
    for result in (runbook_result, handoff_result):
        for ref in result.get("evidence_refs", []):
            if ref and ref not in evidence_refs:
                evidence_refs.append(ref)
    return evidence_refs


def run_materialization(repo_root, payload):
    approval_status_result = payload.get("approval_status_result", {})
    approval_writeback_result = payload.get("approval_writeback_result", {})
    materialization_context = payload.get("materialization_context", {})

    built = BUILDER.build_real_knowledge_payload(
        approval_status_result=approval_status_result,
        approval_writeback_result=approval_writeback_result,
        materialization_context=materialization_context,
    )
    written = MATERIALIZE.materialize_real_knowledge_assets(
        repo_root=repo_root,
        payload=built,
        approval_status_result=approval_status_result,
        approval_writeback_result=approval_writeback_result,
    )

    runbook_result = written["runbook"]
    handoff_result = written["handoff"]
    index_update_status = "skipped"
    failure_reason = ""

    if (
        runbook_result.get("write_status") == "success"
        and handoff_result.get("write_status") == "success"
    ):
        try:
            index_result = UPDATE.update_knowledge_indexes(
                repo_root=repo_root,
                runbook_entry={
                    "title": built["runbook"]["title"],
                    "path": built["runbook"]["target_path"],
                    "purpose": _entry_purpose(built["runbook"]["title"], "runbook"),
                },
                handoff_entry={
                    "title": built["handoff"]["title"],
                    "path": built["handoff"]["target_path"],
                    "purpose": _entry_purpose(built["handoff"]["title"], "handoff"),
                },
            )
            runbook_result["index_status"] = index_result["runbook_index_status"]
            handoff_result["index_status"] = index_result["handoff_index_status"]
            index_update_status = "success"
        except Exception as exc:
            runbook_result["index_status"] = "failed"
            handoff_result["index_status"] = "failed"
            index_update_status = "failed"
            failure_reason = str(exc)
    else:
        failure_reason = "materialization_incomplete"

    materialization_status = "success" if (
        runbook_result.get("write_status") == "success"
        and handoff_result.get("write_status") == "success"
        and runbook_result.get("index_status") == "success"
        and handoff_result.get("index_status") == "success"
    ) else "failed"

    if materialization_status == "failed" and not failure_reason:
        failure_reason = "index_update_failed"

    return {
        "source_refs": built.get("source_refs", {}),
        "runbook": runbook_result,
        "handoff": handoff_result,
        "index_update_status": index_update_status,
        "materialization_status": materialization_status,
        "evidence_refs": _collect_evidence_refs(runbook_result, handoff_result),
        "failure_reason": failure_reason,
    }


def main():
    payload = json.load(sys.stdin)
    result = run_materialization(repo_root=HERE.parent, payload=payload)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

import json
from typing import Any, Dict, Iterable, List, Tuple


def _iter_changed_files(report: Dict[str, Any]) -> Iterable[Tuple[str, List[str]]]:
    by_module = report.get("changed_files_by_module") or {}
    if not isinstance(by_module, dict):
        return []
    for module in sorted(by_module.keys()):
        files = by_module.get(module) or []
        if isinstance(files, list):
            yield module, [str(f) for f in files]


def format_report_md(report: Dict[str, Any]) -> str:
    reason_codes = report.get("reason_codes") or []
    if not isinstance(reason_codes, list):
        reason_codes = []

    lines: List[str] = []
    lines.append("# Drift Guard Report")
    lines.append("")
    lines.append(f"- Mode: {report.get('mode')}")
    lines.append(f"- Change Class: {report.get('change_class')}")
    lines.append(f"- Verdict: {'PASS' if not reason_codes else 'BLOCK'}")
    lines.append(f"- Reason Codes: {', '.join(reason_codes) if reason_codes else 'NONE'}")
    lines.append("")
    lines.append("## Changed Files By Module")
    lines.append("")

    any_files = False
    for module, files in _iter_changed_files(report):
        any_files = True
        lines.append(f"### {module}")
        for path in files:
            lines.append(f"- {path}")
        lines.append("")
    if not any_files:
        lines.append("- NONE")
        lines.append("")

    lines.append("## Required Docs (sha256)")
    lines.append("")
    docs = report.get("docs_hashes") or {}
    if isinstance(docs, dict) and docs:
        for path in sorted(docs.keys()):
            lines.append(f"- {path}: {docs.get(path)}")
    else:
        lines.append("- NONE")
    lines.append("")

    lines.append("## Raw JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)

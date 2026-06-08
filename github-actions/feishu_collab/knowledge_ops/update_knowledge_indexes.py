from pathlib import Path


ENTRIES_HEADING = "## Entries"
RUNBOOK_TABLE_HEADER = "| Runbook | Path | Purpose |"
HANDOFF_TABLE_HEADER = "| Handoff | Path | Purpose |"
TABLE_SEPARATOR = "| --- | --- | --- |"


def _build_row(entry):
    return f"| {entry['title']} | `{entry['path']}` | {entry['purpose']} |"


def _ensure_entries_table(lines, table_header):
    if ENTRIES_HEADING not in lines:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend([ENTRIES_HEADING, "", table_header, TABLE_SEPARATOR])
        return lines

    heading_index = lines.index(ENTRIES_HEADING)
    search_start = heading_index + 1

    if table_header not in lines[search_start:]:
        insert_at = heading_index + 1
        while insert_at < len(lines) and lines[insert_at] == "":
            insert_at += 1
        lines[insert_at:insert_at] = ["", table_header, TABLE_SEPARATOR]
        return lines

    header_index = lines.index(table_header, search_start)
    separator_index = header_index + 1
    if separator_index >= len(lines) or lines[separator_index] != TABLE_SEPARATOR:
        lines.insert(separator_index, TABLE_SEPARATOR)

    return lines


def _replace_or_insert_entry(text, entry, table_header):
    lines = text.splitlines()
    lines = _ensure_entries_table(lines, table_header)

    row_prefix = f"| {entry['title']} |"
    cleaned_lines = [line for line in lines if not line.startswith(row_prefix)]

    header_index = cleaned_lines.index(table_header)
    separator_index = header_index + 1
    cleaned_lines.insert(separator_index + 1, _build_row(entry))

    return "\n".join(cleaned_lines) + "\n"


def update_knowledge_indexes(repo_root, runbook_entry, handoff_entry):
    repo_root = Path(repo_root)
    runbook_index_path = repo_root / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md"
    handoff_index_path = repo_root / "docs" / "feishu-collab" / "HANDOFF_INDEX.md"

    runbook_text = runbook_index_path.read_text(encoding="utf-8")
    runbook_index_path.write_text(
        _replace_or_insert_entry(runbook_text, runbook_entry, RUNBOOK_TABLE_HEADER),
        encoding="utf-8",
    )

    handoff_text = handoff_index_path.read_text(encoding="utf-8")
    handoff_index_path.write_text(
        _replace_or_insert_entry(handoff_text, handoff_entry, HANDOFF_TABLE_HEADER),
        encoding="utf-8",
    )

    return {
        "runbook_index_status": "success",
        "handoff_index_status": "success",
    }

import re


REQUIRED_FIELDS = [
    "Acceptance Request ID:",
    "Acceptance Cycle ID:",
    "Work Item ID:",
    "Request Type:",
    "Request Mode:",
    "Source of Truth:",
    "Target PR:",
    "Lark Base URL:",
    "Lark Table ID:",
    "Lark Record ID:",
]

REQUIRED_SECTIONS = [
    "## 验收对象",
    "## 验收范围",
    "## 业务上下文映射",
    "## 重点验收项",
    "## 本轮不要求",
    "## 期望回写格式",
]


def extract_field(comment_body: str, field_name: str) -> str:
    pattern = rf"{re.escape(field_name)}:\s*(.+)"
    match = re.search(pattern, comment_body)
    return match.group(1).strip() if match else ""


def evaluate_acceptance_request(comment_body: str) -> dict:
    if "[验收委托 / ACCEPTANCE_REQUEST]" not in comment_body:
        return {
            "decision": "BLOCK",
            "protocol_read_result": "FAIL",
            "source_of_truth_verdict": "invalid",
            "reason_codes": ["RULE_ACCEPTANCE_ANCHOR_MISSING"],
            "recommended_next_action": "author: post a valid ACCEPTANCE_REQUEST comment",
        }

    missing_fields = [field for field in REQUIRED_FIELDS if field not in comment_body]
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in comment_body]

    if missing_fields or missing_sections:
        return {
            "decision": "REWORK",
            "protocol_read_result": "PARTIAL",
            "source_of_truth_verdict": "ambiguous",
            "reason_codes": [
                *["RULE_ACCEPTANCE_FIELD_MISSING" for _ in missing_fields],
                *["RULE_ACCEPTANCE_SECTION_MISSING" for _ in missing_sections],
            ],
            "recommended_next_action": "author: complete the missing ACCEPTANCE_REQUEST fields and sections",
        }

    return {
        "decision": "ACCEPTED",
        "protocol_read_result": "PASS",
        "source_of_truth_verdict": "usable",
        "reason_codes": ["NONE"],
        "recommended_next_action": "context-reader: collect lark work item snapshot",
        "acceptance_request_id": extract_field(comment_body, "Acceptance Request ID"),
        "acceptance_cycle_id": extract_field(comment_body, "Acceptance Cycle ID"),
        "work_item_id": extract_field(comment_body, "Work Item ID"),
        "lark_base_url": extract_field(comment_body, "Lark Base URL"),
        "lark_table_id": extract_field(comment_body, "Lark Table ID"),
        "lark_record_id": extract_field(comment_body, "Lark Record ID"),
    }

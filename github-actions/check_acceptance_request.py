import re


REQUIRED_FIELDS = [
    "Acceptance Request ID:",
    "Request Type:",
    "Request Mode:",
    "Source of Truth:",
    "Target PR:",
]

REQUIRED_SECTIONS = [
    "## 验收对象",
    "## 验收范围",
    "## 业务上下文映射",
    "## 重点验收项",
    "## 本轮不要求",
    "## 期望回写格式",
]


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

    match = re.search(r"Acceptance Request ID:\s*(.+)", comment_body)
    request_id = match.group(1).strip() if match else "none"

    return {
        "decision": "ACCEPTED",
        "protocol_read_result": "PASS",
        "source_of_truth_verdict": "usable",
        "reason_codes": ["NONE"],
        "recommended_next_action": "validator: post VALIDATION_RESULT",
        "acceptance_request_id": request_id,
    }

import json
import os
import re
from pathlib import Path


def extract_acceptance_request_id(comment_body: str) -> str:
    match = re.search(r"Acceptance Request ID:\s*(.+)", comment_body)
    return match.group(1).strip() if match else ""


def resolve_issue_comment_event(event: dict) -> dict:
    comment_body = event.get("comment", {}).get("body", "")
    return {
        "pr_number": str(event.get("issue", {}).get("number", "")),
        "acceptance_request_id": extract_acceptance_request_id(comment_body),
        "comment_body": comment_body,
    }


def resolve_issue_comment_event_path(event_path: Path) -> dict:
    event = json.loads(event_path.read_text(encoding="utf-8"))
    return resolve_issue_comment_event(event)


def main() -> None:
    result = resolve_issue_comment_event_path(Path(os.environ["GITHUB_EVENT_PATH"]))
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
        fh.write(f"pr_number={result['pr_number']}\n")
        fh.write(f"acceptance_request_id={result['acceptance_request_id']}\n")


if __name__ == "__main__":
    main()

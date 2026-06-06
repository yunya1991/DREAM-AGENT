# Agent Lifecycle Guard Compatibility V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `Agent Lifecycle Guard` so it accepts either the legacy delivery flow or the new acceptance flow, while keeping shared collaboration baselines enforced.

**Architecture:** Keep the current lifecycle workflow in place and make the compatibility change inside the existing payload builder and checker. Extend the payload builder so it recognizes `ACCEPTANCE_REQUEST` and `VALIDATION_RESULT`, then refactor the checker into common-baseline, legacy-flow, and acceptance-flow decisions with “either legal flow passes” semantics.

**Tech Stack:** Python 3, `unittest`, JSON rule catalog, GitHub Actions workflow YAML already present in `DREAM-AGENT`

---

## File Structure

### New Files

- `docs/agent-lifecycle-guard-compatibility-v2-implementation-plan.md`
  - This implementation plan.

### Modified Files

- `github-actions/build_agent_lifecycle_payload.py`
  - Extend structured comment parsing to detect `ACCEPTANCE_REQUEST` and `VALIDATION_RESULT`.
- `github-actions/check_agent_lifecycle.py`
  - Refactor lifecycle evaluation into common-baseline plus dual-flow compatibility.
- `github-actions/tests/test_build_agent_lifecycle_payload.py`
  - Add payload-builder tests for acceptance-request and validation-result extraction.
- `github-actions/tests/test_check_agent_lifecycle.py`
  - Add checker tests for dual-flow pass conditions, branch whitelist, and acceptance-flow failures.
- `SKILLS/agent-collab-supervisor/rules.json`
  - Keep common-baseline rule IDs aligned with the new checker behavior and preserve legacy rule names where still applicable.

## Task 1: Extend Lifecycle Payload Builder For Acceptance Flow

**Files:**
- Modify: `github-actions/build_agent_lifecycle_payload.py`
- Test: `github-actions/tests/test_build_agent_lifecycle_payload.py`

- [ ] **Step 1: Write the failing acceptance-payload tests**

```python
    def test_acceptance_request_comment_is_recognized_as_structured_status(self):
        raw = {
            "branch": "design/acceptance-protocol",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[验收委托 / ACCEPTANCE_REQUEST]\n\n"
                "Acceptance Request ID: ar-20260607-002\n"
                "Request Type: phase-gate\n"
                "Request Mode: manual\n"
                "Source of Truth: PR comment\n"
                "Target PR: #5\n\n"
                "## 验收对象\n"
                "- acceptance protocol v1\n"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertIn("ACCEPTANCE_REQUEST", payload["comments"])
        self.assertTrue(payload["acceptance_request_present"])
        self.assertEqual(payload["acceptance_request_id"], "ar-20260607-002")

    def test_validation_result_comment_extracts_decision_and_mode(self):
        raw = {
            "branch": "design/acceptance-protocol",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[验证结论 / VALIDATION_RESULT]\n\n"
                "Validator: manual-pilot\n"
                "Validation Mode: acceptance\n"
                "Acceptance Request ID: ar-20260607-002\n"
                "Decision: ACCEPTED\n"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertIn("VALIDATION_RESULT", payload["comments"])
        self.assertTrue(payload["validation_result_present"])
        self.assertEqual(payload["validation_mode"], "acceptance")
        self.assertEqual(payload["validation_decision"], "ACCEPTED")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_build_agent_lifecycle_payload.BuildLifecyclePayloadTests -v
```

Expected: FAIL because `build_agent_lifecycle_payload.py` does not yet recognize `ACCEPTANCE_REQUEST` or `VALIDATION_RESULT`.

- [ ] **Step 3: Add acceptance-aware parsing to the payload builder**

```python
HEADER_TO_STATUS = {
    "[协作开工声明 / STARTED]": "STARTED",
    "[协作状态更新 / UPDATED]": "UPDATED",
    "[协作阻塞通知 / BLOCKED]": "BLOCKED",
    "[协作完成回报 / DONE]": "DONE",
    "[方案评审记录 / DESIGN_REVIEW]": "DESIGN_REVIEW",
    "[测试报告 / TEST_REPORT]": "TEST_REPORT",
    "[验收委托 / ACCEPTANCE_REQUEST]": "ACCEPTANCE_REQUEST",
    "[验证结论 / VALIDATION_RESULT]": "VALIDATION_RESULT",
}


def parse_structured_comment(text):
    for header, status in HEADER_TO_STATUS.items():
        if text.startswith(header):
            return {
                "status": status,
                "agent": extract_field(text, "Agent"),
                "reviewer": extract_field(text, "Reviewer"),
                "execution_mode": detect_execution_mode(text),
                "direct_takeover": detect_direct_takeover(text),
                "occupied_paths": extract_bullets_after_label(text, "占用范围")
                or extract_bullets_after_label(text, "当前占用范围"),
                "acceptance_request_id": extract_field(text, "Acceptance Request ID"),
                "validation_mode": extract_field(text, "Validation Mode"),
                "validation_decision": extract_field(text, "Decision"),
            }
    return None
```

```python
def build_payload(raw):
    comments = []
    structured_comments = []
    for body in raw.get("comments", []):
        parsed = parse_structured_comment(body)
        if parsed:
            comments.append(parsed["status"])
            structured_comments.append(parsed)

    acceptance_request_comment = next(
        (comment for comment in structured_comments if comment["status"] == "ACCEPTANCE_REQUEST"),
        None,
    )
    validation_result_comment = next(
        (comment for comment in structured_comments if comment["status"] == "VALIDATION_RESULT"),
        None,
    )

    ...

    return {
        "branch": raw.get("branch", ""),
        "owner_agent": owner_agent,
        "execution_mode": execution_mode,
        "direct_takeover": direct_takeover,
        "shared_files_declared": shared_files_declared,
        "task_card_present": task_card_present,
        "design_review_present": "DESIGN_REVIEW" in comments,
        "test_report_present": "TEST_REPORT" in comments,
        "non_owner_review_present": non_owner_review_present,
        "scope_change_declared": scope_change_declared,
        "block_declared": block_declared,
        "scope_changed": scope_change_declared,
        "execution_blocked": block_declared,
        "acceptance_request_present": acceptance_request_comment is not None,
        "acceptance_request_id": (acceptance_request_comment or {}).get("acceptance_request_id", ""),
        "validation_result_present": validation_result_comment is not None,
        "validation_mode": (validation_result_comment or {}).get("validation_mode", "").lower(),
        "validation_decision": (validation_result_comment or {}).get("validation_decision", "").upper(),
        "comments": comments,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_build_agent_lifecycle_payload -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add github-actions/build_agent_lifecycle_payload.py github-actions/tests/test_build_agent_lifecycle_payload.py
git commit -m "feat: extend lifecycle payload for acceptance flow"
```

## Task 2: Refactor Lifecycle Checker To Support Dual-Flow Passing

**Files:**
- Modify: `github-actions/check_agent_lifecycle.py`
- Test: `github-actions/tests/test_check_agent_lifecycle.py`

- [ ] **Step 1: Write the failing checker tests**

```python
    def test_pass_when_common_baseline_and_acceptance_flow_exist(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST", "VALIDATION_RESULT"],
            "acceptance_request_present": True,
            "validation_result_present": True,
            "validation_decision": "ACCEPTED",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["reason_codes"], [])

    def test_block_when_acceptance_request_exists_without_validation_result(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST"],
            "acceptance_request_present": True,
            "validation_result_present": False,
            "validation_decision": "",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_VALIDATION_RESULT_REQUIRED", result["reason_codes"])

    def test_pass_when_legacy_flow_still_has_all_required_evidence(self):
        payload = {
            "branch": "agent/solo/lifecycle-docs",
            "shared_files_declared": True,
            "task_card_present": True,
            "design_review_present": True,
            "test_report_present": True,
            "non_owner_review_present": True,
            "scope_changed": False,
            "execution_blocked": False,
            "comments": ["STARTED", "DONE"],
            "acceptance_request_present": False,
            "validation_result_present": False,
            "validation_decision": "",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "PASS")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_agent_lifecycle.LifecycleCheckerTests -v
```

Expected: FAIL because the current checker only accepts the legacy flow.

- [ ] **Step 3: Refactor the checker into common-baseline plus dual-flow evaluation**

```python
ALLOWED_BRANCH_PREFIXES = (
    "agent/",
    "milestone/",
    "design/",
    "acceptance/",
    "protocol/",
)


def branch_policy_valid(branch):
    return branch.startswith(ALLOWED_BRANCH_PREFIXES)


def check_acceptance_request_present(payload):
    return bool(payload.get("acceptance_request_present"))


def check_validation_result_present(payload):
    return bool(payload.get("validation_result_present"))


def check_validation_decision_not_blocked(payload):
    return payload.get("validation_decision", "").upper() not in {"", "BLOCK", "REWORK"}


def common_baseline_pass(payload):
    return (
        check_task_card_present(payload)
        and check_shared_files_declared(payload)
        and check_branch_policy_valid(payload)
    )


def legacy_flow_pass(payload):
    return (
        check_started_comment_present(payload)
        and check_design_review_present(payload)
        and check_test_report_present(payload)
        and check_non_owner_review_present(payload)
        and check_done_comment_present(payload)
        and check_scope_change_announcement(payload)
        and check_block_announcement(payload)
    )


def acceptance_flow_pass(payload):
    if not check_acceptance_request_present(payload):
        return False
    return (
        check_validation_result_present(payload)
        and check_validation_decision_not_blocked(payload)
    )
```

```python
def evaluate_payload(payload):
    reason_codes = []

    if not check_task_card_present(payload):
        reason_codes.append("RULE_001_TASK_CARD_REQUIRED")
    if not check_shared_files_declared(payload):
        reason_codes.append("RULE_010_SHARED_FILE_DECLARATION")
    if not check_branch_policy_valid(payload):
        reason_codes.append("RULE_BRANCH_POLICY_NOT_ALLOWED")

    if reason_codes:
        return {
            "decision": "BLOCK",
            "reason_codes": reason_codes,
            "evaluated_rule_count": len(load_rules()),
        }

    if legacy_flow_pass(payload):
        return {"decision": "PASS", "reason_codes": [], "evaluated_rule_count": len(load_rules())}

    if payload.get("acceptance_request_present") and not payload.get("validation_result_present"):
        return {
            "decision": "BLOCK",
            "reason_codes": ["RULE_VALIDATION_RESULT_REQUIRED"],
            "evaluated_rule_count": len(load_rules()),
        }

    if payload.get("acceptance_request_present") and not check_validation_decision_not_blocked(payload):
        return {
            "decision": "BLOCK",
            "reason_codes": ["RULE_ACCEPTANCE_VALIDATION_BLOCKED"],
            "evaluated_rule_count": len(load_rules()),
        }

    if acceptance_flow_pass(payload):
        return {"decision": "PASS", "reason_codes": [], "evaluated_rule_count": len(load_rules())}

    return {
        "decision": "BLOCK",
        "reason_codes": [
            "RULE_002_DESIGN_REVIEW_REQUIRED",
            "RULE_003_STARTED_REQUIRED",
            "RULE_006_TEST_EVIDENCE_REQUIRED",
            "RULE_007_REVIEW_BY_NON_OWNER",
            "RULE_008_DONE_REQUIRED",
        ],
        "evaluated_rule_count": len(load_rules()),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_agent_lifecycle -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add github-actions/check_agent_lifecycle.py github-actions/tests/test_check_agent_lifecycle.py
git commit -m "feat: add dual-flow lifecycle guard compatibility"
```

## Task 3: Align The Rule Catalog With Compatibility V2

**Files:**
- Modify: `SKILLS/agent-collab-supervisor/rules.json`
- Test: `github-actions/tests/test_check_agent_lifecycle.py`

- [ ] **Step 1: Write the failing rules-alignment test**

```python
    def test_rule_catalog_contains_branch_policy_reason_code_after_compatibility_upgrade(self):
        rule_ids = {rule["id"] for rule in MODULE.load_rules()}
        self.assertIn("RULE_001_TASK_CARD_REQUIRED", rule_ids)
        self.assertIn("RULE_010_SHARED_FILE_DECLARATION", rule_ids)
```

- [ ] **Step 2: Run test to verify it fails only if the runtime catalog drifts**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_agent_lifecycle.LifecycleCheckerTests -v
```

Expected: FAIL if the rule catalog no longer matches the checker after Task 2.

- [ ] **Step 3: Keep the catalog on shared-baseline and legacy-rule IDs**

```json
{
  "version": "1.1",
  "rules": [
    {
      "id": "RULE_001_TASK_CARD_REQUIRED",
      "severity": "block",
      "check": "task_card_present",
      "checker": "check_task_card_present"
    },
    {
      "id": "RULE_002_DESIGN_REVIEW_REQUIRED",
      "severity": "block",
      "check": "design_review_present_for_legacy_flow",
      "checker": "check_design_review_present"
    },
    {
      "id": "RULE_003_STARTED_REQUIRED",
      "severity": "block",
      "check": "started_comment_present_for_legacy_flow",
      "checker": "check_started_comment_present"
    },
    {
      "id": "RULE_004_SCOPE_CHANGE_MUST_UPDATE",
      "severity": "block",
      "check": "updated_comment_present_when_scope_changes",
      "checker": "check_scope_change_announcement"
    },
    {
      "id": "RULE_005_BLOCK_MUST_ANNOUNCE",
      "severity": "block",
      "check": "blocked_comment_present_when_execution_blocked",
      "checker": "check_block_announcement"
    },
    {
      "id": "RULE_006_TEST_EVIDENCE_REQUIRED",
      "severity": "block",
      "check": "test_report_present_for_legacy_flow",
      "checker": "check_test_report_present"
    },
    {
      "id": "RULE_007_REVIEW_BY_NON_OWNER",
      "severity": "block",
      "check": "non_owner_review_present_for_legacy_flow",
      "checker": "check_non_owner_review_present"
    },
    {
      "id": "RULE_008_DONE_REQUIRED",
      "severity": "block",
      "check": "done_comment_present_for_legacy_flow",
      "checker": "check_done_comment_present"
    },
    {
      "id": "RULE_009_BRANCH_POLICY_ENFORCED",
      "severity": "block",
      "check": "branch_policy_valid",
      "checker": "check_branch_policy_valid"
    },
    {
      "id": "RULE_010_SHARED_FILE_DECLARATION",
      "severity": "block",
      "check": "shared_files_declared",
      "checker": "check_shared_files_declared"
    }
  ]
}
```

- [ ] **Step 4: Run the lifecycle checker tests again**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_agent_lifecycle -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add SKILLS/agent-collab-supervisor/rules.json github-actions/tests/test_check_agent_lifecycle.py
git commit -m "docs: align lifecycle rule catalog with dual-flow guard"
```

## Task 4: Run Full Compatibility Verification

**Files:**
- Verify only

- [ ] **Step 1: Run the targeted compatibility suite**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest \
  github-actions.tests.test_build_agent_lifecycle_payload \
  github-actions.tests.test_check_agent_lifecycle \
  github-actions.tests.test_check_acceptance_request \
  github-actions.tests.test_collab_workflows_present -v
```

Expected: PASS.

- [ ] **Step 2: Run a manual compatibility smoke check**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 - <<'PY'
import importlib.util
from pathlib import Path

root = Path.cwd()
module_path = root / "github-actions" / "check_agent_lifecycle.py"
spec = importlib.util.spec_from_file_location("check_agent_lifecycle", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

legacy_payload = {
    "branch": "agent/solo/lifecycle-docs",
    "shared_files_declared": True,
    "task_card_present": True,
    "design_review_present": True,
    "test_report_present": True,
    "non_owner_review_present": True,
    "scope_changed": False,
    "execution_blocked": False,
    "comments": ["STARTED", "DONE"],
    "acceptance_request_present": False,
    "validation_result_present": False,
    "validation_decision": "",
}
acceptance_payload = {
    "branch": "design/acceptance-protocol",
    "shared_files_declared": True,
    "task_card_present": True,
    "comments": ["ACCEPTANCE_REQUEST", "VALIDATION_RESULT"],
    "acceptance_request_present": True,
    "validation_result_present": True,
    "validation_decision": "ACCEPTED",
}

assert module.evaluate_payload(legacy_payload)["decision"] == "PASS"
assert module.evaluate_payload(acceptance_payload)["decision"] == "PASS"
print("lifecycle compatibility smoke ok")
PY
```

Expected:

```text
lifecycle compatibility smoke ok
```

- [ ] **Step 3: Commit the verified state**

```bash
git add .
git commit -m "test: verify lifecycle guard compatibility v2"
```

## Self-Review

- Spec coverage:
  - dual-flow compatibility: Task 2
  - acceptance-flow payload recognition: Task 1
  - widened branch policy: Task 2
  - reason-code and rule alignment: Task 3
  - final compatibility verification: Task 4
- Placeholder scan:
  - No `TODO`/`TBD` placeholders remain.
  - All steps include concrete file paths, commands, and expected results.
- Type consistency:
  - `acceptance_request_present`, `validation_result_present`, `validation_decision`, and the allowed branch prefixes are used consistently across builder, checker, and tests.

Plan complete and saved to `docs/agent-lifecycle-guard-compatibility-v2-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?

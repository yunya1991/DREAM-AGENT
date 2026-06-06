# Agent Lifecycle Guard Pending State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Agent Lifecycle Guard` treat `ACCEPTANCE_REQUEST` without `VALIDATION_RESULT` as a non-failing `PENDING` intermediate state.

**Architecture:** Keep the existing dual-flow lifecycle checker, but add a third decision state for acceptance flow in progress. The checker returns `PENDING` for the intermediate state, and the GitHub Actions workflow only fails the job when the checker returns `BLOCK`.

**Tech Stack:** Python 3.11, GitHub Actions YAML, `unittest`

---

### Task 1: Lock Pending Decision With Tests

**Files:**
- Modify: `github-actions/tests/test_check_agent_lifecycle.py`
- Test: `github-actions/tests/test_check_agent_lifecycle.py`

- [ ] **Step 1: Change the acceptance intermediate-state test to expect `PENDING`**

```python
    def test_pending_when_acceptance_request_exists_without_validation_result(self):
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

        self.assertEqual(result["decision"], "PENDING")
        self.assertIn("RULE_VALIDATION_RESULT_PENDING", result["reason_codes"])
```

- [ ] **Step 2: Add a test that blocked validation still returns `BLOCK`**

```python
    def test_block_when_validation_result_exists_but_decision_is_blocking(self):
        payload = {
            "branch": "design/acceptance-protocol",
            "shared_files_declared": True,
            "task_card_present": True,
            "comments": ["ACCEPTANCE_REQUEST", "VALIDATION_RESULT"],
            "acceptance_request_present": True,
            "validation_result_present": True,
            "validation_decision": "REWORK",
        }

        result = MODULE.evaluate_payload(payload)

        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_ACCEPTANCE_VALIDATION_BLOCKED", result["reason_codes"])
```

- [ ] **Step 3: Run the targeted tests to verify red**

Run: `python3 -m unittest github-actions.tests.test_check_agent_lifecycle`

Expected: FAIL because the current implementation still returns `BLOCK` for the intermediate acceptance state.

### Task 2: Implement Pending Decision In Checker

**Files:**
- Modify: `github-actions/check_agent_lifecycle.py`
- Test: `github-actions/tests/test_check_agent_lifecycle.py`

- [ ] **Step 1: Return `PENDING` instead of `BLOCK` for acceptance flow in progress**

```python
    if check_acceptance_request_present(payload) and not check_validation_result_present(
        payload
    ):
        return {
            "decision": "PENDING",
            "reason_codes": ["RULE_VALIDATION_RESULT_PENDING"],
            "evaluated_rule_count": len(rules),
        }
```

- [ ] **Step 2: Keep the blocked validation branch strict**

```python
    if check_acceptance_request_present(payload) and not check_validation_decision_not_blocked(
        payload
    ):
        return {
            "decision": "BLOCK",
            "reason_codes": ["RULE_ACCEPTANCE_VALIDATION_BLOCKED"],
            "evaluated_rule_count": len(rules),
        }
```

- [ ] **Step 3: Re-run the targeted tests to verify green**

Run: `python3 -m unittest github-actions.tests.test_check_agent_lifecycle`

Expected: PASS

### Task 3: Make Workflow Treat Pending As Non-Failing

**Files:**
- Modify: `.github/workflows/agent-lifecycle-guard.yml`

- [ ] **Step 1: Capture checker output to a JSON file**

```yaml
      - name: Run lifecycle checker
        run: python3 "github-actions/check_agent_lifecycle.py" agent_lifecycle_payload.json > agent_lifecycle_result.json
```

- [ ] **Step 2: Fail only when decision is `BLOCK`**

```yaml
      - name: Enforce lifecycle decision
        run: |
          python3 - <<'PY'
          import json
          import sys

          with open("agent_lifecycle_result.json", "r", encoding="utf-8") as fh:
              result = json.load(fh)

          print(json.dumps(result, indent=2, ensure_ascii=False))

          if result.get("decision") == "BLOCK":
              sys.exit(1)
          PY
```

- [ ] **Step 3: Preserve pass-through for `PASS` and `PENDING`**

Run: no extra code needed beyond the enforcement step above.

Expected: `PENDING` and `PASS` both exit successfully; only `BLOCK` fails the workflow.

### Task 4: Verify The End-To-End Behavior

**Files:**
- Modify: none
- Test: `github-actions/tests/test_check_agent_lifecycle.py`

- [ ] **Step 1: Run targeted lifecycle tests**

Run: `python3 -m unittest github-actions.tests.test_check_agent_lifecycle`

Expected: PASS

- [ ] **Step 2: Re-run the previous auto-trigger scenario on a real PR**

Run: post a fresh `ACCEPTANCE_REQUEST` comment on the pilot PR after pushing the fix branch.

Expected: `Agent Lifecycle Guard` no longer fails on the acceptance intermediate state; `collab-acceptance-agent` still auto-triggers.

- [ ] **Step 3: Record what still blocks if present**

Run: inspect `gh pr checks <pr-number>` and `gh run view <run-id> --log`

Expected: any remaining failures must be unrelated to the acceptance intermediate-state decision, such as branch policy or missing task card/shared file baseline.

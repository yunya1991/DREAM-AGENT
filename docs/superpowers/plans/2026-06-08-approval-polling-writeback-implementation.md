# Approval Polling Writeback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated approval-polling-writeback workflow that reads a real approval instance status, projects it into the normalized approval/automation states, writes task and goal records back to Feishu Base, emits artifacts plus Job Summary, and fails only after preserving writeback evidence.

**Architecture:** Keep the workflow thin and reuse the existing approval query and Base writeback scripts as the operational core. First normalize approval status semantics in the shared approval API layer, then refactor the existing polling writeback adapter so it can accept a precomputed status projection and return structured receipts, then add one dedicated runner, one workflow-only summary helper, one standalone `.github/workflows/approval-polling-writeback.yml`, and operator docs wired into the runbook index.

**Tech Stack:** Python 3, `unittest`, GitHub Actions YAML, existing `feishu_approval_api.py`, existing `query_real_approval_status.py`, existing `poll_feishu_approval_and_sync_base.py`, existing `sync_github_to_feishu.py`, existing `build_goal_progress_record.py`, JSON artifacts, Markdown Job Summary

---

## Scope Check

This plan covers one coherent sub-project:

- Normalize approval status projection to match the approved third-phase design
- Refactor the existing polling writeback adapter into a reusable status-first writeback path
- Add a dedicated runner that produces `approval_writeback_result.json`
- Add a workflow-only summary helper and standalone `workflow_dispatch` workflow
- Add an operator runbook and register it in `RUNBOOK_INDEX.md`
- Validate the end-to-end polling/writeback baseline with targeted tests and a local dry-run

It does **not** include:

- Real approval creation
- Background daemons or timed polling services
- Knowledge materialization
- Acceptance-workflow integration
- Rehearsal-workflow integration
- Multi-workflow orchestration

## File Map

- Modify: `github-actions/feishu_approval_api.py`
  - Normalize `approval_status -> automation_status` projection so approved results map to `proceed` and rejected results map to `blocked`.
- Modify: `github-actions/tests/test_feishu_approval_api.py`
  - Lock the new normalized automation-state mapping.
- Modify: `github-actions/tests/test_query_real_approval_status.py`
  - Keep the standalone query wrapper aligned with the normalized approval projection.
- Modify: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`
  - Lock the updated automation-state writeback behavior and new partial-failure evidence behavior.
- Modify: `github-actions/poll_feishu_approval_and_sync_base.py`
  - Extract a reusable `sync_with_status_result()` path that consumes a precomputed approval status result, returns task/goal receipts, and preserves partial failure evidence.
- Create: `github-actions/run_approval_polling_writeback.py`
  - Read a workflow payload that already contains `status_result`, call the refactored writeback adapter, and emit a normalized `approval_writeback_result`.
- Create: `github-actions/tests/test_run_approval_polling_writeback.py`
  - Lock the runner payload shape and `approval_writeback_result` structure.
- Create: `github-actions/render_approval_polling_writeback_summary.py`
  - Read `approval_status_result.json` and `approval_writeback_result.json`, render Job Summary markdown, and return workflow exit code from query-plus-writeback success.
- Create: `github-actions/tests/test_render_approval_polling_writeback_summary.py`
  - Lock summary content and workflow exit semantics.
- Create: `.github/workflows/approval-polling-writeback.yml`
  - Dedicated `workflow_dispatch` entrypoint for query, writeback, summary, and artifact upload.
- Create: `github-actions/tests/test_approval_polling_writeback_workflow.py`
  - Lock workflow presence, required inputs, query/writeback/summary helper calls, and `if: always()` artifact upload behavior.
- Create: `docs/feishu-collab/runbooks/approval-polling-writeback.md`
  - Operator-facing runbook for inputs, artifacts, success/failure interpretation, and common recovery steps.
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
  - Register the new operator runbook so the polling/writeback path is discoverable.
- Modify: `docs/feishu-collab/runbooks/real-approval-trigger.md`
  - Add a short “next step” note pointing operators from instance creation to polling/writeback.
- Create: `github-actions/tests/test_approval_polling_writeback_docs.py`
  - Lock runbook coverage, index registration, and the cross-reference from the real trigger runbook.

## Execution Guardrails

- Do not duplicate approval query logic inside the new workflow; reuse `query_real_approval_status.py`.
- Do not query the approval instance twice in the new workflow; the writeback runner must consume the precomputed `status_result`.
- Keep `real-approval-trigger.yml` unchanged as the create-plus-one-shot-query entrypoint; the new workflow is a separate operational stage.
- Keep task writeback ahead of goal writeback. If task writeback fails, do not attempt goal writeback.
- Preserve partial evidence when goal writeback fails: the workflow must still emit the task receipt and a failed `goal_writeback_status`.
- Keep knowledge materialization out of this plan; artifacts and summary are the only outputs for the next phase to consume.
- Keep operational routing explicit via `base_sync_json`; do not hide Base writeback coordinates in hard-coded YAML values.

## Task 1: Normalize Approval Projection Semantics

**Files:**
- Modify: `github-actions/feishu_approval_api.py`
- Modify: `github-actions/tests/test_feishu_approval_api.py`
- Modify: `github-actions/tests/test_query_real_approval_status.py`
- Modify: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`

- [ ] **Step 1: Write the failing normalization tests**

Update `github-actions/tests/test_feishu_approval_api.py` so the projection test becomes:

```python
    def test_resolve_instance_status_maps_to_normalized_automation_states(self):
        SPEC.loader.exec_module(MODULE)
        approved = MODULE.resolve_instance_status({"status": "APPROVED"}, decision_id="decision-001")
        rejected = MODULE.resolve_instance_status({"status": "REJECTED"}, decision_id="decision-002")
        pending = MODULE.resolve_instance_status({"status": "PENDING"}, decision_id="decision-003")

        self.assertEqual(approved["approval_status"], "approved")
        self.assertEqual(approved["automation_status"], "proceed")
        self.assertEqual(approved["decision_summary"], "approved:decision-001")

        self.assertEqual(rejected["approval_status"], "rejected")
        self.assertEqual(rejected["automation_status"], "blocked")
        self.assertEqual(rejected["decision_summary"], "rejected:decision-002")

        self.assertEqual(pending["approval_status"], "pending")
        self.assertEqual(pending["automation_status"], "paused")
        self.assertEqual(pending["decision_summary"], "pending:decision-003")
```

Update `github-actions/tests/test_query_real_approval_status.py`:

```python
    def test_build_status_result_uses_normalized_status_projection(self):
        module = self.load_module()
        result = module.build_status_result(
            instance={"status": "APPROVED"},
            decision_id="TASK-1",
            instance_code="ins_123",
        )
        self.assertEqual(result["approval_instance_code"], "ins_123")
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["automation_status"], "proceed")
        self.assertEqual(result["decision_summary"], "approved:TASK-1")
```

Update the relevant assertions in `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`:

```python
        self.assertEqual(result["task_updates"]["approval_status"], "approved")
        self.assertEqual(result["task_updates"]["automation_status"], "proceed")
```

and:

```python
        task_fields = mock_upsert.call_args_list[0].args[3]
        self.assertEqual(task_fields["审批状态"], "rejected")
        self.assertEqual(task_fields["自动化状态"], "blocked")
        self.assertEqual(task_fields["审批决策ID"], "task-2")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_query_real_approval_status.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: FAIL because the current projection still returns `running` for approved and `paused` for rejected.

- [ ] **Step 3: Write the minimal normalization implementation**

Update `github-actions/feishu_approval_api.py`:

```python
def resolve_instance_status(instance, decision_id):
    status = instance.get("status", "PENDING")
    if status == "APPROVED":
        return {
            "approval_status": "approved",
            "automation_status": "proceed",
            "decision_summary": f"approved:{decision_id}",
        }
    if status == "REJECTED":
        return {
            "approval_status": "rejected",
            "automation_status": "blocked",
            "decision_summary": f"rejected:{decision_id}",
        }
    if status == "NOT_REQUIRED":
        return {
            "approval_status": "not_required",
            "automation_status": "proceed",
            "decision_summary": f"not_required:{decision_id}",
        }
    return {
        "approval_status": "pending",
        "automation_status": "paused",
        "decision_summary": f"pending:{decision_id}",
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_query_real_approval_status.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: PASS with all approval projection and polling writeback assertions green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_approval_api.py \
        github-actions/tests/test_feishu_approval_api.py \
        github-actions/tests/test_query_real_approval_status.py \
        github-actions/tests/test_poll_feishu_approval_and_sync_base.py
git commit -m "feat: normalize approval polling statuses"
```

## Task 2: Refactor the Writeback Adapter and Add the Polling Runner

**Files:**
- Modify: `github-actions/poll_feishu_approval_and_sync_base.py`
- Modify: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`
- Create: `github-actions/run_approval_polling_writeback.py`
- Create: `github-actions/tests/test_run_approval_polling_writeback.py`

- [ ] **Step 1: Write the failing adapter and runner tests**

Append these tests to `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`:

```python
    @patch.object(POLL, "upsert_base_record")
    def test_task_writeback_failure_skips_goal_writeback(self, mock_upsert):
        mock_upsert.side_effect = RuntimeError("task writeback failed")

        result = POLL.sync_with_status_result(
            payload={
                "task_payload": {
                    "task_id": "task-fail",
                    "task_name": "Task Fail",
                    "goal_id": "goal-fail",
                },
                "goal_payload": {
                    "goal_id": "goal-fail",
                    "goal_name": "Goal Fail",
                    "goal_owner": "owner",
                },
                "sibling_tasks": [],
                "base_sync": {
                    "base_token": "app_base",
                    "task_table_id": "tbl_task",
                    "task_record_id": "rec_task",
                    "goal_table_id": "tbl_goal",
                    "goal_record_id": "rec_goal",
                },
            },
            status_result={
                "approval_instance_code": "instance-fail",
                "approval_status": "approved",
                "automation_status": "proceed",
                "decision_summary": "approved:task-fail",
            },
        )

        self.assertEqual(result["task_writeback_status"], "failed")
        self.assertEqual(result["goal_writeback_status"], "skipped")
        self.assertEqual(mock_upsert.call_count, 1)

    @patch.object(POLL, "upsert_base_record")
    def test_goal_writeback_failure_preserves_task_receipt(self, mock_upsert):
        mock_upsert.side_effect = [
            {"record_id": "rec_task_written"},
            RuntimeError("goal writeback failed"),
        ]

        result = POLL.sync_with_status_result(
            payload={
                "task_payload": {
                    "task_id": "task-goal-fail",
                    "task_name": "Task Goal Fail",
                    "goal_id": "goal-goal-fail",
                },
                "goal_payload": {
                    "goal_id": "goal-goal-fail",
                    "goal_name": "Goal Goal Fail",
                    "goal_owner": "owner",
                },
                "sibling_tasks": [],
                "base_sync": {
                    "base_token": "app_base",
                    "task_table_id": "tbl_task",
                    "task_record_id": "rec_task",
                    "goal_table_id": "tbl_goal",
                    "goal_record_id": "rec_goal",
                },
            },
            status_result={
                "approval_instance_code": "instance-goal-fail",
                "approval_status": "approved",
                "automation_status": "proceed",
                "decision_summary": "approved:task-goal-fail",
            },
        )

        self.assertEqual(result["task_writeback_status"], "success")
        self.assertEqual(result["goal_writeback_status"], "failed")
        self.assertEqual(result["task_writeback_receipt"]["record_id"], "rec_task_written")
```

Create `github-actions/tests/test_run_approval_polling_writeback.py`:

```python
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_approval_polling_writeback.py"
SPEC = importlib.util.spec_from_file_location("run_approval_polling_writeback", MODULE_PATH)


class RunApprovalPollingWritebackTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_payload(self):
        return {
            "task_payload": {"task_id": "TASK-1"},
            "goal_payload": {"goal_id": "GOAL-1"},
            "status_result": {
                "approval_instance_code": "ins_123",
                "approval_status": "approved",
                "automation_status": "proceed",
                "decision_summary": "approved:TASK-1",
            },
        }

    @patch("run_approval_polling_writeback.POLL.sync_with_status_result")
    def test_build_writeback_result_contains_statuses_and_receipts(self, mock_sync):
        mock_sync.return_value = {
            "task_record": {"任务ID": "TASK-1"},
            "goal_record": {"goal_id": "GOAL-1"},
            "task_writeback_status": "success",
            "goal_writeback_status": "success",
            "task_writeback_receipt": {"record_id": "rec_task"},
            "goal_writeback_receipt": {"record_id": "rec_goal"},
        }
        module = self.load_module()
        result = module.run_writeback(self.sample_payload())
        self.assertEqual(result["task_id"], "TASK-1")
        self.assertEqual(result["goal_id"], "GOAL-1")
        self.assertEqual(result["task_writeback_status"], "success")
        self.assertEqual(result["goal_writeback_status"], "success")
        self.assertEqual(result["writeback_receipts"]["task"]["record_id"], "rec_task")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
  github-actions/tests/test_run_approval_polling_writeback.py -v
```

Expected:

- FAIL because `sync_with_status_result()` does not exist yet
- FAIL because `run_approval_polling_writeback.py` does not exist yet

- [ ] **Step 3: Write the minimal adapter and runner**

Update `github-actions/poll_feishu_approval_and_sync_base.py`:

```python
def sync_with_status_result(payload, status_result):
    base_sync = payload["base_sync"]
    task_updates = dict(payload["task_payload"])
    task_updates.update(status_result)
    task_updates.setdefault("approval_decision_id", task_updates.get("task_id", ""))

    task_record = SYNC.build_feishu_record(task_updates)
    goal_payload = payload["goal_payload"]
    goal_record = GOAL.build_goal_record(goal_payload, [task_updates, *payload["sibling_tasks"]])

    try:
        task_receipt = upsert_base_record(
            base_sync["base_token"],
            base_sync["task_table_id"],
            base_sync["task_record_id"],
            task_record,
        )
    except Exception as exc:
        return {
            "task_updates": task_updates,
            "task_record": task_record,
            "goal_record": goal_record,
            "task_writeback_status": "failed",
            "goal_writeback_status": "skipped",
            "task_writeback_receipt": {},
            "goal_writeback_receipt": {},
            "error": str(exc),
        }

    try:
        goal_receipt = upsert_base_record(
            base_sync["base_token"],
            base_sync["goal_table_id"],
            base_sync["goal_record_id"],
            goal_record,
        )
    except Exception as exc:
        return {
            "task_updates": task_updates,
            "task_record": task_record,
            "goal_record": goal_record,
            "task_writeback_status": "success",
            "goal_writeback_status": "failed",
            "task_writeback_receipt": task_receipt,
            "goal_writeback_receipt": {},
            "error": str(exc),
        }

    return {
        "task_updates": task_updates,
        "task_record": task_record,
        "goal_record": goal_record,
        "task_writeback_status": "success",
        "goal_writeback_status": "success",
        "task_writeback_receipt": task_receipt,
        "goal_writeback_receipt": goal_receipt,
    }


def poll_and_sync(payload):
    instance_code = payload["approval_instance_code"]
    instance = APPROVAL_API.get_instance(payload["tenant_access_token"], instance_code)
    status_result = APPROVAL_API.build_status_projection(
        instance,
        decision_id=payload["task_payload"].get("approval_decision_id", payload["task_payload"].get("task_id", "")),
        instance_code=instance_code,
    )
    return sync_with_status_result(payload, status_result)
```

Create `github-actions/run_approval_polling_writeback.py`:

```python
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def load_module(name, file_name):
    path = HERE / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLL = load_module("poll_feishu_approval_and_sync_base", "poll_feishu_approval_and_sync_base.py")


def run_writeback(payload):
    sync_result = POLL.sync_with_status_result(
        payload={
            "task_payload": payload.get("task_payload", {}),
            "goal_payload": payload.get("goal_payload", {}),
            "sibling_tasks": payload.get("sibling_tasks", []),
            "base_sync": payload.get("base_sync", {}),
        },
        status_result=payload.get("status_result", {}),
    )
    return {
        "task_id": payload.get("task_payload", {}).get("task_id", ""),
        "goal_id": payload.get("goal_payload", {}).get("goal_id", ""),
        "task_record": sync_result.get("task_record", {}),
        "goal_record": sync_result.get("goal_record", {}),
        "task_writeback_status": sync_result.get("task_writeback_status", ""),
        "goal_writeback_status": sync_result.get("goal_writeback_status", ""),
        "writeback_receipts": {
            "task": sync_result.get("task_writeback_receipt", {}),
            "goal": sync_result.get("goal_writeback_receipt", {}),
        },
        "error": sync_result.get("error", ""),
    }


def main():
    payload = json.load(sys.stdin)
    json.dump(run_writeback(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
  github-actions/tests/test_run_approval_polling_writeback.py -v
```

Expected: PASS with the new partial-failure evidence tests and the standalone writeback runner test green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/poll_feishu_approval_and_sync_base.py \
        github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
        github-actions/run_approval_polling_writeback.py \
        github-actions/tests/test_run_approval_polling_writeback.py
git commit -m "feat: add approval polling writeback runner"
```

## Task 3: Add the Summary Helper and Standalone Workflow

**Files:**
- Create: `github-actions/render_approval_polling_writeback_summary.py`
- Create: `github-actions/tests/test_render_approval_polling_writeback_summary.py`
- Create: `.github/workflows/approval-polling-writeback.yml`
- Create: `github-actions/tests/test_approval_polling_writeback_workflow.py`

- [ ] **Step 1: Write the failing summary and workflow tests**

Create `github-actions/tests/test_render_approval_polling_writeback_summary.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_approval_polling_writeback_summary.py"
SPEC = importlib.util.spec_from_file_location(
    "render_approval_polling_writeback_summary",
    MODULE_PATH,
)


class RenderApprovalPollingWritebackSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_status(self):
        return {
            "approval_instance_code": "ins_123",
            "approval_status": "approved",
            "automation_status": "proceed",
            "decision_summary": "approved:TASK-1",
        }

    def sample_writeback(self, task_status="success", goal_status="success"):
        return {
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "task_writeback_status": task_status,
            "goal_writeback_status": goal_status,
            "writeback_receipts": {
                "task": {"record_id": "rec_task"},
                "goal": {"record_id": "rec_goal"},
            },
        }

    def test_build_summary_markdown_renders_core_statuses(self):
        module = self.load_module()
        summary = module.build_summary_markdown(self.sample_status(), self.sample_writeback())
        self.assertIn("ins_123", summary)
        self.assertIn("approved", summary)
        self.assertIn("proceed", summary)
        self.assertIn("TASK-1", summary)
        self.assertIn("success", summary)

    def test_workflow_exit_code_requires_query_and_both_writebacks(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_status(), self.sample_writeback()), 0)
        self.assertEqual(module.workflow_exit_code({}, self.sample_writeback()), 1)
        self.assertEqual(module.workflow_exit_code(self.sample_status(), self.sample_writeback(goal_status="failed")), 1)
```

Create `github-actions/tests/test_approval_polling_writeback_workflow.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ApprovalPollingWritebackWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "approval-polling-writeback.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "approval-polling-writeback.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_declares_required_inputs(self):
        text = self.read_workflow()
        self.assertIn("approval_instance_code:", text)
        self.assertIn("decision_id:", text)
        self.assertIn("task_payload_json:", text)
        self.assertIn("goal_payload_json:", text)
        self.assertIn("base_sync_json:", text)

    def test_workflow_calls_query_writeback_and_summary_helpers(self):
        text = self.read_workflow()
        self.assertIn("python3 github-actions/query_real_approval_status.py", text)
        self.assertIn("python3 github-actions/run_approval_polling_writeback.py", text)
        self.assertIn("python3 github-actions/render_approval_polling_writeback_summary.py", text)

    def test_workflow_uploads_artifacts_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("approval_status_result.json", text)
        self.assertIn("approval_writeback_result.json", text)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_render_approval_polling_writeback_summary.py \
  github-actions/tests/test_approval_polling_writeback_workflow.py -v
```

Expected: FAIL because the summary helper and the workflow do not exist yet.

- [ ] **Step 3: Write the minimal summary helper and workflow**

Create `github-actions/render_approval_polling_writeback_summary.py`:

```python
import json
import os
from pathlib import Path
import sys


def build_summary_markdown(status_result, writeback_result):
    lines = [
        "# Approval Polling Writeback",
        "",
        f"- Approval Instance Code: `{status_result.get('approval_instance_code', '')}`",
        f"- Approval Status: `{status_result.get('approval_status', '')}`",
        f"- Automation Status: `{status_result.get('automation_status', '')}`",
        f"- Task ID: `{writeback_result.get('task_id', '')}`",
        f"- Goal ID: `{writeback_result.get('goal_id', '')}`",
        f"- Task Writeback: `{writeback_result.get('task_writeback_status', '')}`",
        f"- Goal Writeback: `{writeback_result.get('goal_writeback_status', '')}`",
        f"- Decision Summary: `{status_result.get('decision_summary', '')}`",
        "",
    ]
    return "\n".join(lines)


def workflow_exit_code(status_result, writeback_result):
    return 0 if (
        status_result.get("approval_status")
        and writeback_result.get("task_writeback_status") == "success"
        and writeback_result.get("goal_writeback_status") == "success"
    ) else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    status_path = Path(argv[0])
    writeback_path = Path(argv[1])
    status_result = json.loads(status_path.read_text(encoding="utf-8"))
    writeback_result = json.loads(writeback_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(status_result, writeback_result)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")
    else:
        sys.stdout.write(summary + "\n")
    raise SystemExit(workflow_exit_code(status_result, writeback_result))


if __name__ == "__main__":
    main()
```

Create `.github/workflows/approval-polling-writeback.yml`:

```yaml
name: approval-polling-writeback

on:
  workflow_dispatch:
    inputs:
      approval_instance_code:
        description: Existing approval instance code
        required: true
        type: string
      decision_id:
        description: Decision id used for status projection
        required: true
        type: string
      task_payload_json:
        description: Task payload JSON
        required: true
        type: string
      goal_payload_json:
        description: Goal payload JSON
        required: true
        type: string
      base_sync_json:
        description: Base sync routing JSON
        required: true
        type: string
      sibling_tasks_json:
        description: Optional sibling tasks JSON array
        required: false
        default: "[]"
        type: string

permissions:
  contents: read

jobs:
  approval-polling-writeback:
    runs-on: [self-hosted, macOS, workbuddy]
    steps:
      - name: Checkout workflow ref
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Initialize result placeholders
        run: |
          printf '{}\n' > approval_status_result.json
          printf '{}\n' > approval_writeback_result.json

      - name: Mint lark tenant access token
        env:
          LARK_APP_ID: ${{ secrets.LARK_APP_ID }}
          LARK_APP_SECRET: ${{ secrets.LARK_APP_SECRET }}
        run: |
          python3 - <<'PY'
          import json
          import os
          import urllib.request

          payload = json.dumps(
              {"app_id": os.environ["LARK_APP_ID"], "app_secret": os.environ["LARK_APP_SECRET"]}
          ).encode("utf-8")
          request = urllib.request.Request(
              "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
              data=payload,
              headers={"Content-Type": "application/json; charset=utf-8"},
              method="POST",
          )
          with urllib.request.urlopen(request) as response:
              result = json.loads(response.read().decode("utf-8"))
          if result.get("code") != 0 or not result.get("tenant_access_token"):
              raise SystemExit(json.dumps(result, ensure_ascii=False))
          print(f"::add-mask::{result['tenant_access_token']}")
          with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as fh:
              fh.write(f"LARK_TENANT_ACCESS_TOKEN={result['tenant_access_token']}\n")
          PY

      - name: Build approval status query payload
        env:
          APPROVAL_INSTANCE_CODE: ${{ inputs.approval_instance_code }}
          DECISION_ID: ${{ inputs.decision_id }}
          LARK_TENANT_ACCESS_TOKEN: ${{ env.LARK_TENANT_ACCESS_TOKEN }}
        run: |
          python3 - <<'PY' > approval_status_input.json
          import json
          import os

          payload = {
              "tenant_access_token": os.environ["LARK_TENANT_ACCESS_TOKEN"],
              "approval_instance_code": os.environ["APPROVAL_INSTANCE_CODE"],
              "decision_id": os.environ["DECISION_ID"],
          }
          print(json.dumps(payload, ensure_ascii=False))
          PY

      - name: Query approval status
        run: |
          python3 github-actions/query_real_approval_status.py < approval_status_input.json > approval_status_result.json

      - name: Build polling writeback payload
        env:
          TASK_PAYLOAD_JSON: ${{ inputs.task_payload_json }}
          GOAL_PAYLOAD_JSON: ${{ inputs.goal_payload_json }}
          BASE_SYNC_JSON: ${{ inputs.base_sync_json }}
          SIBLING_TASKS_JSON: ${{ inputs.sibling_tasks_json }}
        run: |
          python3 - <<'PY' > approval_writeback_input.json
          import json
          import os
          from pathlib import Path

          payload = {
              "task_payload": json.loads(os.environ["TASK_PAYLOAD_JSON"]),
              "goal_payload": json.loads(os.environ["GOAL_PAYLOAD_JSON"]),
              "base_sync": json.loads(os.environ["BASE_SYNC_JSON"]),
              "sibling_tasks": json.loads(os.environ["SIBLING_TASKS_JSON"]),
              "status_result": json.loads(Path("approval_status_result.json").read_text(encoding="utf-8")),
          }
          print(json.dumps(payload, ensure_ascii=False))
          PY

      - name: Run approval polling writeback
        run: |
          python3 github-actions/run_approval_polling_writeback.py < approval_writeback_input.json > approval_writeback_result.json

      - name: Render polling writeback summary
        if: always()
        run: |
          python3 github-actions/render_approval_polling_writeback_summary.py approval_status_result.json approval_writeback_result.json

      - name: Upload polling writeback artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: approval-polling-writeback-${{ github.run_id }}
          path: |
            approval_status_result.json
            approval_writeback_result.json
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_render_approval_polling_writeback_summary.py \
  github-actions/tests/test_approval_polling_writeback_workflow.py -v
```

Expected: PASS with summary content and workflow contract assertions green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/render_approval_polling_writeback_summary.py \
        github-actions/tests/test_render_approval_polling_writeback_summary.py \
        .github/workflows/approval-polling-writeback.yml \
        github-actions/tests/test_approval_polling_writeback_workflow.py
git commit -m "feat: add approval polling writeback workflow"
```

## Task 4: Add the Operator Runbook and Index Entries

**Files:**
- Create: `docs/feishu-collab/runbooks/approval-polling-writeback.md`
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
- Modify: `docs/feishu-collab/runbooks/real-approval-trigger.md`
- Create: `github-actions/tests/test_approval_polling_writeback_docs.py`

- [ ] **Step 1: Write the failing docs contract test**

Create `github-actions/tests/test_approval_polling_writeback_docs.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ApprovalPollingWritebackDocsTests(unittest.TestCase):
    def test_polling_runbook_mentions_workflow_inputs_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "approval-polling-writeback.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/approval-polling-writeback.yml", text)
        self.assertIn("approval_instance_code", text)
        self.assertIn("base_sync_json", text)
        self.assertIn("approval_status_result.json", text)
        self.assertIn("approval_writeback_result.json", text)

    def test_runbook_index_registers_polling_writeback_entry(self):
        text = (REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("Approval Polling Writeback", text)
        self.assertIn("approval-polling-writeback.md", text)

    def test_real_approval_trigger_runbook_points_to_polling_follow_up(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "real-approval-trigger.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/approval-polling-writeback.yml", text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_approval_polling_writeback_docs.py -v
```

Expected: FAIL because the new runbook does not exist, the runbook index has no entry yet, and the real approval trigger runbook has no follow-up note.

- [ ] **Step 3: Write the runbook and index updates**

Create `docs/feishu-collab/runbooks/approval-polling-writeback.md`:

```md
# Approval Polling Writeback

## Purpose

Query an existing Feishu approval instance, project the result into normalized approval fields, and write the latest task and goal state back to Feishu Base.

## Workflow Entry

- Workflow: `.github/workflows/approval-polling-writeback.yml`
- Trigger: `workflow_dispatch`
- Required inputs:
  - `approval_instance_code`
  - `decision_id`
  - `task_payload_json`
  - `goal_payload_json`
  - `base_sync_json`
- Optional inputs:
  - `sibling_tasks_json`

## Secrets

- `LARK_APP_ID`
- `LARK_APP_SECRET`

## Artifacts

- `approval_status_result.json`
- `approval_writeback_result.json`

## Success Rule

The workflow succeeds only when the approval query returns a valid status and both the task and goal writebacks succeed.

## Failure Guide

- If the query fails, inspect `approval_status_result.json` first.
- If task writeback fails, fix the task writeback route and rerun before touching goal writeback.
- If goal writeback fails, keep the task receipt, repair the goal route, and rerun.
```

Update the entries table in `docs/feishu-collab/RUNBOOK_INDEX.md` to:

```md
| Runbook | Path | Purpose |
| --- | --- | --- |
| Five Skill Integration Rehearsal | `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` | Run the fixture-driven full-chain rehearsal and interpret the normalized result |
| Real Approval Trigger | `docs/feishu-collab/runbooks/real-approval-trigger.md` | Create a real approval instance and capture the first approval-status evidence |
| Approval Polling Writeback | `docs/feishu-collab/runbooks/approval-polling-writeback.md` | Query an existing approval instance and write the normalized task/goal state back to Base |
```

Append this note to `docs/feishu-collab/runbooks/real-approval-trigger.md`:

```md
## Next Step

After the approval instance exists, use `.github/workflows/approval-polling-writeback.yml` to continue from status evidence into task/goal writeback.
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_approval_polling_writeback_docs.py -v
```

Expected: PASS with runbook, index, and cross-reference assertions green.

- [ ] **Step 5: Commit**

```bash
git add docs/feishu-collab/runbooks/approval-polling-writeback.md \
        docs/feishu-collab/RUNBOOK_INDEX.md \
        docs/feishu-collab/runbooks/real-approval-trigger.md \
        github-actions/tests/test_approval_polling_writeback_docs.py
git commit -m "docs: add approval polling writeback runbook"
```

## Task 5: Validate the Full Polling Writeback Baseline

**Files:**
- Modify: `github-actions/poll_feishu_approval_and_sync_base.py`
- Modify: `github-actions/run_approval_polling_writeback.py`
- Modify: `github-actions/render_approval_polling_writeback_summary.py`
- Modify: `.github/workflows/approval-polling-writeback.yml`
- Modify: `docs/feishu-collab/runbooks/approval-polling-writeback.md`

- [ ] **Step 1: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_feishu_approval_api_contract.py \
  github-actions/tests/test_query_real_approval_status.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
  github-actions/tests/test_run_approval_polling_writeback.py \
  github-actions/tests/test_render_approval_polling_writeback_summary.py \
  github-actions/tests/test_approval_polling_writeback_workflow.py \
  github-actions/tests/test_approval_polling_writeback_docs.py -v
```

Expected: all approval polling, writeback, workflow, and docs tests PASS.

- [ ] **Step 2: Perform the local workflow-style dry-run**

Run:

```bash
python3 -c 'import json, pathlib; pathlib.Path("approval_status_result.json").write_text(json.dumps({"approval_instance_code":"ins_local","approval_status":"approved","automation_status":"proceed","decision_summary":"approved:TASK-LOCAL"}, ensure_ascii=False), encoding="utf-8")'
python3 -c 'import json, subprocess, pathlib; payload={"task_payload":{"task_id":"TASK-LOCAL","task_name":"Local Polling","goal_id":"GOAL-LOCAL","risk_level":"high"},"goal_payload":{"goal_id":"GOAL-LOCAL","goal_name":"Local Goal","goal_owner":"governance-agent","next_milestone":"verify writeback"},"base_sync":{"base_token":"app_base","task_table_id":"tbl_task","task_record_id":"rec_task","goal_table_id":"tbl_goal","goal_record_id":"rec_goal"},"sibling_tasks":[],"status_result":json.loads(pathlib.Path("approval_status_result.json").read_text(encoding="utf-8"))}; result=subprocess.run(["python3","github-actions/run_approval_polling_writeback.py"], input=json.dumps(payload, ensure_ascii=False).encode("utf-8"), stdout=subprocess.PIPE, check=True); pathlib.Path("approval_writeback_result.json").write_bytes(result.stdout)'
GITHUB_STEP_SUMMARY=/tmp/approval-polling-writeback-summary.md python3 github-actions/render_approval_polling_writeback_summary.py approval_status_result.json approval_writeback_result.json
python3 -c 'import json, pathlib; status=json.loads(pathlib.Path("approval_status_result.json").read_text(encoding="utf-8")); writeback=json.loads(pathlib.Path("approval_writeback_result.json").read_text(encoding="utf-8")); summary=pathlib.Path("/tmp/approval-polling-writeback-summary.md").read_text(encoding="utf-8"); assert status["approval_instance_code"]=="ins_local"; assert writeback["task_id"]=="TASK-LOCAL"; assert writeback["task_writeback_status"] in {"success","failed"}; assert "Approval Polling Writeback" in summary; assert "TASK-LOCAL" in summary; print("approval polling writeback dry-run ok")'
```

Expected:

- `approval_status_result.json` exists
- `approval_writeback_result.json` exists
- `/tmp/approval-polling-writeback-summary.md` exists
- the terminal prints `approval polling writeback dry-run ok`

- [ ] **Step 3: Commit**

```bash
git add github-actions/feishu_approval_api.py \
        github-actions/tests/test_feishu_approval_api.py \
        github-actions/tests/test_query_real_approval_status.py \
        github-actions/poll_feishu_approval_and_sync_base.py \
        github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
        github-actions/run_approval_polling_writeback.py \
        github-actions/tests/test_run_approval_polling_writeback.py \
        github-actions/render_approval_polling_writeback_summary.py \
        github-actions/tests/test_render_approval_polling_writeback_summary.py \
        .github/workflows/approval-polling-writeback.yml \
        github-actions/tests/test_approval_polling_writeback_workflow.py \
        docs/feishu-collab/runbooks/approval-polling-writeback.md \
        docs/feishu-collab/RUNBOOK_INDEX.md \
        docs/feishu-collab/runbooks/real-approval-trigger.md \
        github-actions/tests/test_approval_polling_writeback_docs.py
git commit -m "test: validate approval polling writeback baseline"
```

## Self-Review

- Spec coverage:
  - independent polling workflow: Task 3
  - normalized approval status and automation-state mapping: Task 1
  - fixed task-before-goal writeback order and partial-failure evidence: Task 2
  - artifacts, summary, and workflow exit semantics: Task 3
  - runbook/index/operator discoverability: Task 4
  - local dry-run and targeted regression coverage: Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred markers
  - Every code-bearing step includes concrete code or YAML
  - Every verification step includes exact commands and expected outcomes
- Type consistency:
  - workflow file stays `.github/workflows/approval-polling-writeback.yml`
  - status artifact stays `approval_status_result.json`
  - writeback artifact stays `approval_writeback_result.json`
  - standalone runner stays `github-actions/run_approval_polling_writeback.py`
  - summary helper stays `github-actions/render_approval_polling_writeback_summary.py`
  - workflow inputs stay `approval_instance_code`, `decision_id`, `task_payload_json`, `goal_payload_json`, `base_sync_json`, `sibling_tasks_json`

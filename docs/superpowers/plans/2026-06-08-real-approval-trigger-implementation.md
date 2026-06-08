# Real Approval Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated real-approval workflow that creates a Feishu approval instance through the existing Python approval orchestration path, queries the new instance status once, emits artifacts and Job Summary, and fails only after preserving approval evidence.

**Architecture:** Keep the workflow thin and move all approval behavior into small Python entrypoints that reuse the existing approval API wrapper and orchestration script. Add a dispatcher wrapper for real approval creation, add a one-shot query wrapper for the created instance, add a workflow-only summary renderer, then wire them into a new standalone `.github/workflows/real-approval-trigger.yml` that remains parallel to rehearsal and acceptance flows.

**Tech Stack:** Python 3, `unittest`, GitHub Actions YAML, existing `feishu_approval_api.py`, existing `run_goal_progress_approval_cycle.py`, JSON artifacts, Markdown Job Summary

---

## Scope Check

This plan covers one coherent sub-project:

- Add a dispatcher wrapper for real approval creation
- Add a query wrapper for one-shot approval status lookup
- Add a summary helper for artifact and Job Summary rendering
- Add a dedicated `workflow_dispatch` real-approval workflow
- Validate the real-approval trigger baseline with contract tests and local dry-run

It does **not** include:

- Periodic polling
- Base writeback
- Knowledge materialization
- Acceptance workflow integration
- Rehearsal workflow integration

## File Map

- Create: `github-actions/run_real_approval_dispatch.py`
  - Reads workflow payload, calls `run_goal_progress_approval_cycle.run_cycle()`, and writes a normalized dispatch result including created instance code and request evidence.
- Create: `github-actions/query_real_approval_status.py`
  - Reads `tenant_access_token`, `instance_code`, and `decision_id`, then calls `feishu_approval_api.get_instance()` and `build_status_projection()`.
- Create: `github-actions/render_real_approval_summary.py`
  - Renders approval result markdown to `GITHUB_STEP_SUMMARY` and returns `0/1` based on creation-plus-query success.
- Create: `github-actions/tests/test_run_real_approval_dispatch.py`
  - Locks dispatch payload normalization and created-instance result structure.
- Create: `github-actions/tests/test_query_real_approval_status.py`
  - Locks query result shape and approval status projection.
- Create: `github-actions/tests/test_render_real_approval_summary.py`
  - Locks summary content and workflow exit semantics.
- Create: `.github/workflows/real-approval-trigger.yml`
  - Dedicated `workflow_dispatch` workflow for real approval creation and one-shot status query.
- Create: `github-actions/tests/test_real_approval_trigger_workflow.py`
  - Locks workflow presence, required inputs, dispatcher/query usage, and `if: always()` artifact upload.
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
  - Add a short cross-reference to the separate real-approval workflow so operators do not confuse rehearsal with real execution.
- Create: `docs/feishu-collab/runbooks/real-approval-trigger.md`
  - Operator-facing runbook for required inputs, secrets, outputs, and failure interpretation.
- Create: `github-actions/tests/test_real_approval_trigger_docs.py`
  - Locks that the new runbook mentions the workflow file, required inputs, artifacts, and “evidence first” behavior.

## Execution Guardrails

- Do not keep or expand workflow-inline HTTP logic for real approval creation; use Python wrappers only.
- Reuse `feishu_approval_api.py` and `run_goal_progress_approval_cycle.py` instead of cloning approval logic into new files.
- Preserve artifacts on all outcomes with `if: always()`.
- Treat this workflow as independent from both rehearsal and acceptance workflows.
- Query only once after creation in this stage; do not introduce retry loops or timers.
- Keep approval input normalization explicit and deterministic so a later polling/writeback stage can reuse it.

## Task 1: Add the Real Approval Dispatch Wrapper

**Files:**
- Create: `github-actions/run_real_approval_dispatch.py`
- Create: `github-actions/tests/test_run_real_approval_dispatch.py`

- [ ] **Step 1: Write the failing dispatch tests**

Create `github-actions/tests/test_run_real_approval_dispatch.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_real_approval_dispatch.py"
SPEC = importlib.util.spec_from_file_location("run_real_approval_dispatch", MODULE_PATH)


class RunRealApprovalDispatchTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_dispatch_payload_prefers_open_id_and_preserves_ids(self):
        module = self.load_module()
        payload = module.build_dispatch_payload(
            approval_code="approval-code",
            applicant_open_id="ou_123",
            tenant_access_token="tenant-token",
            task_payload={"task_id": "TASK-1"},
            goal_payload={"goal_id": "GOAL-1"},
        )
        self.assertEqual(payload["approval_code"], "approval-code")
        self.assertEqual(payload["applicant_open_id"], "ou_123")
        self.assertEqual(payload["task_payload"]["task_id"], "TASK-1")
        self.assertEqual(payload["goal_payload"]["goal_id"], "GOAL-1")

    def test_build_dispatch_result_extracts_created_instance_and_state(self):
        module = self.load_module()
        result = module.build_dispatch_result(
            dispatch_payload={
                "approval_code": "approval-code",
                "task_payload": {"task_id": "TASK-1"},
                "goal_payload": {"goal_id": "GOAL-1"},
            },
            cycle_result={
                "task_updates": {
                    "approval_instance_code": "ins_123",
                    "approval_status": "pending",
                    "automation_status": "paused",
                    "decision_summary": "approval_created",
                },
                "task_record": {"任务ID": "TASK-1"},
                "goal_record": {"目标ID": "GOAL-1"},
            },
        )
        self.assertEqual(result["approval_instance_code"], "ins_123")
        self.assertEqual(result["approval_status"], "pending")
        self.assertEqual(result["automation_status"], "paused")
        self.assertEqual(result["decision_summary"], "approval_created")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_real_approval_dispatch.py -v
```

Expected: FAIL because `run_real_approval_dispatch.py` does not exist yet.

- [ ] **Step 3: Write the minimal dispatch wrapper**

Create `github-actions/run_real_approval_dispatch.py`:

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


APPROVAL_CYCLE = load_module("run_goal_progress_approval_cycle", "run_goal_progress_approval_cycle.py")


def build_dispatch_payload(
    approval_code,
    applicant_open_id,
    tenant_access_token,
    task_payload,
    goal_payload,
    sibling_tasks=None,
):
    return {
        "approval_code": approval_code,
        "applicant_open_id": applicant_open_id,
        "tenant_access_token": tenant_access_token,
        "task_payload": task_payload,
        "goal_payload": goal_payload,
        "sibling_tasks": sibling_tasks or [],
    }


def build_dispatch_result(dispatch_payload, cycle_result):
    task_updates = cycle_result["task_updates"]
    return {
        "approval_code": dispatch_payload["approval_code"],
        "task_id": dispatch_payload["task_payload"].get("task_id", ""),
        "goal_id": dispatch_payload["goal_payload"].get("goal_id", ""),
        "approval_instance_code": task_updates.get("approval_instance_code", ""),
        "approval_status": task_updates.get("approval_status", ""),
        "automation_status": task_updates.get("automation_status", ""),
        "decision_summary": task_updates.get("decision_summary", ""),
        "task_record": cycle_result.get("task_record", {}),
        "goal_record": cycle_result.get("goal_record", {}),
        "task_updates": task_updates,
    }


def main():
    payload = json.load(sys.stdin)
    dispatch_payload = build_dispatch_payload(
        approval_code=payload.get("approval_code", ""),
        applicant_open_id=payload.get("applicant_open_id", ""),
        tenant_access_token=payload.get("tenant_access_token", ""),
        task_payload=payload.get("task_payload", {}),
        goal_payload=payload.get("goal_payload", {}),
        sibling_tasks=payload.get("sibling_tasks", []),
    )
    cycle_result = APPROVAL_CYCLE.run_cycle(
        task_payload=dispatch_payload["task_payload"],
        goal_payload=dispatch_payload["goal_payload"],
        sibling_tasks=dispatch_payload["sibling_tasks"],
        tenant_access_token=dispatch_payload["tenant_access_token"],
        approval_code=dispatch_payload["approval_code"],
        applicant_user_id="",
        applicant_open_id=dispatch_payload["applicant_open_id"],
    )
    json.dump(
        build_dispatch_result(dispatch_payload, cycle_result),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_real_approval_dispatch.py -v
```

Expected: PASS with `Ran 2 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/run_real_approval_dispatch.py \
        github-actions/tests/test_run_real_approval_dispatch.py
git commit -m "feat: add real approval dispatch wrapper"
```

## Task 2: Add the One-Shot Query Wrapper and Summary Helper

**Files:**
- Create: `github-actions/query_real_approval_status.py`
- Create: `github-actions/render_real_approval_summary.py`
- Create: `github-actions/tests/test_query_real_approval_status.py`
- Create: `github-actions/tests/test_render_real_approval_summary.py`

- [ ] **Step 1: Write the failing query and summary tests**

Create `github-actions/tests/test_query_real_approval_status.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "query_real_approval_status.py"
SPEC = importlib.util.spec_from_file_location("query_real_approval_status", MODULE_PATH)


class QueryRealApprovalStatusTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_status_result_uses_status_projection(self):
        module = self.load_module()
        result = module.build_status_result(
            instance={"status": "APPROVED"},
            decision_id="TASK-1",
            instance_code="ins_123",
        )
        self.assertEqual(result["approval_instance_code"], "ins_123")
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["automation_status"], "running")
        self.assertEqual(result["decision_summary"], "approved:TASK-1")


if __name__ == "__main__":
    unittest.main()
```

Create `github-actions/tests/test_render_real_approval_summary.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_real_approval_summary.py"
SPEC = importlib.util.spec_from_file_location("render_real_approval_summary", MODULE_PATH)


class RenderRealApprovalSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_dispatch(self):
        return {
            "approval_code": "approval-code",
            "task_id": "TASK-1",
            "goal_id": "GOAL-1",
            "approval_instance_code": "ins_123",
            "approval_status": "pending",
            "automation_status": "paused",
            "decision_summary": "approval_created",
        }

    def sample_query(self, status="pending"):
        return {
            "approval_instance_code": "ins_123",
            "approval_status": status,
            "automation_status": "paused" if status == "pending" else "running",
            "decision_summary": "pending:TASK-1" if status == "pending" else "approved:TASK-1",
        }

    def test_build_summary_markdown_renders_core_approval_fields(self):
        module = self.load_module()
        summary = module.build_summary_markdown(self.sample_dispatch(), self.sample_query())
        self.assertIn("approval-code", summary)
        self.assertIn("ins_123", summary)
        self.assertIn("TASK-1", summary)
        self.assertIn("pending", summary)

    def test_workflow_exit_code_is_zero_only_when_instance_and_status_exist(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_dispatch(), self.sample_query("approved")), 0)
        self.assertEqual(module.workflow_exit_code(self.sample_dispatch(), {}), 1)
        self.assertEqual(module.workflow_exit_code({"approval_instance_code": ""}, self.sample_query()), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_query_real_approval_status.py \
  github-actions/tests/test_render_real_approval_summary.py -v
```

Expected: FAIL because the two target modules do not exist yet.

- [ ] **Step 3: Write the minimal query and summary helpers**

Create `github-actions/query_real_approval_status.py`:

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


APPROVAL_API = load_module("feishu_approval_api", "feishu_approval_api.py")


def build_status_result(instance, decision_id, instance_code):
    result = APPROVAL_API.build_status_projection(instance, decision_id, instance_code)
    result["approval_instance_code"] = instance_code
    return result


def main():
    payload = json.load(sys.stdin)
    instance = APPROVAL_API.get_instance(
        payload.get("tenant_access_token", ""),
        payload.get("approval_instance_code", ""),
    )
    result = build_status_result(
        instance=instance,
        decision_id=payload.get("decision_id", ""),
        instance_code=payload.get("approval_instance_code", ""),
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
```

Create `github-actions/render_real_approval_summary.py`:

```python
import json
import os
from pathlib import Path
import sys


def build_summary_markdown(dispatch_result, query_result):
    lines = [
        "# Real Approval Trigger",
        "",
        f"- Approval Code: `{dispatch_result.get('approval_code', '')}`",
        f"- Task ID: `{dispatch_result.get('task_id', '')}`",
        f"- Goal ID: `{dispatch_result.get('goal_id', '')}`",
        f"- Approval Instance Code: `{query_result.get('approval_instance_code', dispatch_result.get('approval_instance_code', ''))}`",
        f"- Approval Status: `{query_result.get('approval_status', dispatch_result.get('approval_status', ''))}`",
        f"- Automation Status: `{query_result.get('automation_status', dispatch_result.get('automation_status', ''))}`",
        f"- Decision Summary: `{query_result.get('decision_summary', dispatch_result.get('decision_summary', ''))}`",
        "",
    ]
    return "\n".join(lines)


def workflow_exit_code(dispatch_result, query_result):
    return 0 if dispatch_result.get("approval_instance_code") and query_result.get("approval_status") else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    dispatch_path = Path(argv[0])
    query_path = Path(argv[1])
    dispatch_result = json.loads(dispatch_path.read_text(encoding="utf-8"))
    query_result = json.loads(query_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(dispatch_result, query_result)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")
    else:
        sys.stdout.write(summary + "\n")
    raise SystemExit(workflow_exit_code(dispatch_result, query_result))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_query_real_approval_status.py \
  github-actions/tests/test_render_real_approval_summary.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/query_real_approval_status.py \
        github-actions/render_real_approval_summary.py \
        github-actions/tests/test_query_real_approval_status.py \
        github-actions/tests/test_render_real_approval_summary.py
git commit -m "feat: add approval query and summary helpers"
```

## Task 3: Add the Dedicated Real Approval Workflow

**Files:**
- Create: `.github/workflows/real-approval-trigger.yml`
- Create: `github-actions/tests/test_real_approval_trigger_workflow.py`

- [ ] **Step 1: Write the failing workflow contract tests**

Create `github-actions/tests/test_real_approval_trigger_workflow.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RealApprovalTriggerWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "real-approval-trigger.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "real-approval-trigger.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_declares_required_inputs(self):
        text = self.read_workflow()
        self.assertIn("approval_code:", text)
        self.assertIn("applicant_open_id:", text)
        self.assertIn("task_payload_json:", text)
        self.assertIn("goal_payload_json:", text)

    def test_workflow_calls_dispatch_query_and_summary_helpers(self):
        text = self.read_workflow()
        self.assertIn("python3 github-actions/run_real_approval_dispatch.py", text)
        self.assertIn("python3 github-actions/query_real_approval_status.py", text)
        self.assertIn("python3 github-actions/render_real_approval_summary.py", text)

    def test_workflow_uploads_artifacts_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("approval_dispatch_result.json", text)
        self.assertIn("approval_status_result.json", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_real_approval_trigger_workflow.py -v
```

Expected: FAIL because `.github/workflows/real-approval-trigger.yml` does not exist yet.

- [ ] **Step 3: Write the minimal workflow**

Create `.github/workflows/real-approval-trigger.yml`:

```yaml
name: real-approval-trigger

on:
  workflow_dispatch:
    inputs:
      approval_code:
        description: Feishu approval code
        required: true
        type: string
      applicant_open_id:
        description: Applicant open id
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

permissions:
  contents: read

jobs:
  real-approval:
    runs-on: [self-hosted, macOS, workbuddy]
    steps:
      - name: Checkout workflow ref
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

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

      - name: Run real approval dispatch
        env:
          APPROVAL_CODE: ${{ inputs.approval_code }}
          APPLICANT_OPEN_ID: ${{ inputs.applicant_open_id }}
          TASK_PAYLOAD_JSON: ${{ inputs.task_payload_json }}
          GOAL_PAYLOAD_JSON: ${{ inputs.goal_payload_json }}
          LARK_TENANT_ACCESS_TOKEN: ${{ env.LARK_TENANT_ACCESS_TOKEN }}
        run: |
          python3 - <<'PY' > approval_dispatch_result.json
          import json
          import os
          import subprocess

          payload = {
              "approval_code": os.environ["APPROVAL_CODE"],
              "applicant_open_id": os.environ["APPLICANT_OPEN_ID"],
              "tenant_access_token": os.environ["LARK_TENANT_ACCESS_TOKEN"],
              "task_payload": json.loads(os.environ["TASK_PAYLOAD_JSON"]),
              "goal_payload": json.loads(os.environ["GOAL_PAYLOAD_JSON"]),
              "sibling_tasks": [],
          }
          result = subprocess.run(
              ["python3", "github-actions/run_real_approval_dispatch.py"],
              input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
              stdout=subprocess.PIPE,
              check=True,
          )
          print(result.stdout.decode("utf-8"), end="")
          PY

      - name: Query real approval status
        env:
          LARK_TENANT_ACCESS_TOKEN: ${{ env.LARK_TENANT_ACCESS_TOKEN }}
        run: |
          python3 - <<'PY' > approval_status_result.json
          import json
          import os
          import subprocess
          from pathlib import Path

          dispatch = json.loads(Path("approval_dispatch_result.json").read_text(encoding="utf-8"))
          payload = {
              "tenant_access_token": os.environ["LARK_TENANT_ACCESS_TOKEN"],
              "approval_instance_code": dispatch["approval_instance_code"],
              "decision_id": dispatch["task_id"],
          }
          result = subprocess.run(
              ["python3", "github-actions/query_real_approval_status.py"],
              input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
              stdout=subprocess.PIPE,
              check=True,
          )
          print(result.stdout.decode("utf-8"), end="")
          PY

      - name: Render approval summary
        if: always()
        run: |
          python3 github-actions/render_real_approval_summary.py approval_dispatch_result.json approval_status_result.json

      - name: Upload approval artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: real-approval-trigger-${{ github.run_id }}
          path: |
            approval_dispatch_result.json
            approval_status_result.json
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_real_approval_trigger_workflow.py -v
```

Expected: PASS with `Ran 4 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/real-approval-trigger.yml \
        github-actions/tests/test_real_approval_trigger_workflow.py
git commit -m "feat: add real approval trigger workflow"
```

## Task 4: Add the Real Approval Runbook

**Files:**
- Create: `docs/feishu-collab/runbooks/real-approval-trigger.md`
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
- Create: `github-actions/tests/test_real_approval_trigger_docs.py`

- [ ] **Step 1: Write the failing runbook contract test**

Create `github-actions/tests/test_real_approval_trigger_docs.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RealApprovalTriggerDocsTests(unittest.TestCase):
    def test_real_approval_runbook_mentions_workflow_inputs_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "real-approval-trigger.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/real-approval-trigger.yml", text)
        self.assertIn("approval_code", text)
        self.assertIn("applicant_open_id", text)
        self.assertIn("approval_dispatch_result.json", text)
        self.assertIn("approval_status_result.json", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_real_approval_trigger_docs.py -v
```

Expected: FAIL because `real-approval-trigger.md` does not exist yet.

- [ ] **Step 3: Write the runbooks**

Create `docs/feishu-collab/runbooks/real-approval-trigger.md`:

```md
# Real Approval Trigger

## Purpose

Run a real Feishu approval creation flow and immediately query the created instance once.

## Workflow Entry

- Workflow: `.github/workflows/real-approval-trigger.yml`
- Trigger: `workflow_dispatch`
- Required inputs:
  - `approval_code`
  - `applicant_open_id`
  - `task_payload_json`
  - `goal_payload_json`

## Secrets

- `LARK_APP_ID`
- `LARK_APP_SECRET`

## Artifacts

- `approval_dispatch_result.json`
- `approval_status_result.json`

## Success Rule

The workflow succeeds only when the approval instance is created and the follow-up query returns a valid approval status.

## Evidence First

Even on failure, keep the uploaded artifacts and the Job Summary. They are the primary debugging evidence for this stage.
```

Append this short cross-reference to `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`:

```md
## Real Execution Note

For real approval side effects, use `.github/workflows/real-approval-trigger.yml`. The rehearsal workflow remains a dry-run and does not create real approval instances.
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_real_approval_trigger_docs.py -v
```

Expected: PASS with `Ran 1 test ... OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/feishu-collab/runbooks/real-approval-trigger.md \
        docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md \
        github-actions/tests/test_real_approval_trigger_docs.py
git commit -m "docs: add real approval trigger runbook"
```

## Task 5: Validate the Real Approval Trigger Baseline

**Files:**
- Modify: `github-actions/run_real_approval_dispatch.py`
- Modify: `github-actions/query_real_approval_status.py`
- Modify: `github-actions/render_real_approval_summary.py`
- Modify: `.github/workflows/real-approval-trigger.yml`

- [ ] **Step 1: Run the full real-approval contract suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_run_real_approval_dispatch.py \
  github-actions/tests/test_query_real_approval_status.py \
  github-actions/tests/test_render_real_approval_summary.py \
  github-actions/tests/test_real_approval_trigger_workflow.py \
  github-actions/tests/test_real_approval_trigger_docs.py \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_feishu_approval_api_contract.py \
  github-actions/tests/test_run_goal_progress_approval_cycle.py \
  github-actions/tests/test_collab_workflows_present.py -v
```

Expected: all real-approval wrapper, workflow, and approval-script tests PASS.

- [ ] **Step 2: Perform the local workflow-style dry-run with mocked payload**

Run:

```bash
python3 - <<'PY'
import json
import subprocess

dispatch_payload = {
    "approval_code": "approval-code",
    "applicant_open_id": "ou_123",
    "tenant_access_token": "tenant-token",
    "task_payload": {"task_id": "TASK-1", "risk_level": "high"},
    "goal_payload": {"goal_id": "GOAL-1"},
    "sibling_tasks": [],
}

dispatch = subprocess.run(
    ["python3", "github-actions/run_real_approval_dispatch.py"],
    input=json.dumps(dispatch_payload, ensure_ascii=False).encode("utf-8"),
    stdout=subprocess.PIPE,
    check=False,
)
print(dispatch.returncode)
PY
```

Expected:

- wrapper process executes without syntax errors
- if the fake token blocks the real HTTP call, the failure is external-call-related rather than payload-shape-related
- this confirms the local wrapper boundary is valid even before running against real secrets

- [ ] **Step 3: Commit**

```bash
git add github-actions/run_real_approval_dispatch.py \
        github-actions/query_real_approval_status.py \
        github-actions/render_real_approval_summary.py \
        github-actions/tests/test_run_real_approval_dispatch.py \
        github-actions/tests/test_query_real_approval_status.py \
        github-actions/tests/test_render_real_approval_summary.py \
        .github/workflows/real-approval-trigger.yml \
        github-actions/tests/test_real_approval_trigger_workflow.py \
        docs/feishu-collab/runbooks/real-approval-trigger.md \
        docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md \
        github-actions/tests/test_real_approval_trigger_docs.py
git commit -m "test: validate real approval trigger baseline"
```

## Self-Review

- Spec coverage:
  - independent real-approval workflow: Task 3
  - unified Python-script mainline: Tasks 1 and 2
  - one-shot query after creation: Task 2
  - artifact and Job Summary evidence: Tasks 2, 3, and 4
  - next-stage polling/writeback explicitly excluded: Scope Check and Execution Guardrails
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred markers
  - Every code-bearing step includes concrete code or YAML
  - Every verification step includes exact commands and expected outcomes
- Type consistency:
  - workflow file stays `.github/workflows/real-approval-trigger.yml`
  - dispatch artifact stays `approval_dispatch_result.json`
  - query artifact stays `approval_status_result.json`
  - required workflow inputs stay `approval_code`, `applicant_open_id`, `task_payload_json`, `goal_payload_json`

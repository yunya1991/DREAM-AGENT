# Feishu Approval Success Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the real Feishu approval success loop by posting PR evidence, polling approval status back into Base monitor records, suppressing Node 20 action warnings, and updating local Skill plus repo docs.

**Architecture:** Reuse the existing approval API and projection modules instead of inventing a new orchestration path. Keep smoke workflow focused on definition fetch and instance creation, add a separate polling/writeback entrypoint for approval result projection, and treat PR commenting, workflow runtime settings, and documentation updates as isolated follow-up tasks.

**Tech Stack:** Python 3, unittest, GitHub Actions, GitHub CLI, `lark-cli`, Feishu Approval v4 API, Feishu Base via `lark-cli base +record-upsert`

---

## File Map

- Modify: `.github/workflows/collab-acceptance-agent.yml`
  - Add Node 24 runtime override and, if needed, expose artifact-friendly output for approval instance code.
- Modify: `.github/workflows/collab-validator-agent.yml`
  - Add the same Node 24 runtime override because it still uses deprecated JavaScript actions.
- Create: `github-actions/poll_feishu_approval_and_sync_base.py`
  - Query a real approval instance, project the result into task/goal records, and write those records back to Feishu Base.
- Modify: `github-actions/feishu_approval_api.py`
  - Add any minimal helper needed by the poller to keep instance parsing reusable.
- Test: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`
  - Lock the new poll-and-writeback contract.
- Modify: `github-actions/tests/test_collab_workflows_present.py`
  - Extend workflow assertions for Node 24 override.
- Modify: `README.md`
  - Record the successful smoke run, required scopes, and the `open_id` / `form` pitfalls.
- Modify: `docs/04-ENGINEERING-INDEX.md`
  - Register the new closure spec/plan and runtime handling notes.
- Modify: `docs/06-SKILLS-INVENTORY.md`
  - Add a short note that the GitHub x Feishu bootstrap knowledge now includes real approval smoke pitfalls.
- Modify: `/Users/zhangjiangtao/.trae/skills/lark-approval/SKILL.md`
  - Add a “real smoke checklist” section for approval instance creation.

## Constants and Inputs

The implementation should standardize on these runtime inputs for the new poller:

- `LARK_TENANT_ACCESS_TOKEN`
- `APPROVAL_INSTANCE_CODE`
- `FEISHU_MONITOR_BASE_TOKEN`
- `FEISHU_TASK_TABLE_ID`
- `FEISHU_TASK_RECORD_ID`
- `FEISHU_GOAL_TABLE_ID`
- `FEISHU_GOAL_RECORD_ID`

The poller input JSON should look like this:

```json
{
  "tenant_access_token": "tenant-token",
  "approval_instance_code": "188BD557-48FE-460E-8728-BD987112E7D0",
  "task_payload": {
    "task_id": "goal-approval-smoke",
    "task_name": "Feishu approval smoke",
    "goal_id": "goal-feishu-approval",
    "repo": "yunya1991/DREAM-AGENT",
    "approval_status": "pending",
    "approval_instance_code": "188BD557-48FE-460E-8728-BD987112E7D0",
    "approval_decision_id": "goal-approval-smoke",
    "automation_status": "paused"
  },
  "goal_payload": {
    "goal_id": "goal-feishu-approval",
    "goal_name": "Feishu approval closure",
    "goal_owner": "governance-agent",
    "current_phase": "approval-sync",
    "next_milestone": "write back instance state"
  },
  "sibling_tasks": []
}
```

## Task 1: Post Success Evidence to PR #7

**Files:**
- Create: `/tmp/pr7-feishu-approval-success.md` (session-local)

- [ ] **Step 1: Prepare the exact success comment body**

```markdown
UPDATED: Feishu approval real smoke succeeded

- Scope status: `approval:approval` and `approval:instance` are now enabled and verified live.
- Smoke run: https://github.com/yunya1991/DREAM-AGENT/actions/runs/27098459714
- Approval code: `6DE5C07A-5FDC-44D0-9110-8B74AB0837B6`
- Applicant open_id path: confirmed request body must use `open_id`, not `user_id`
- Created instance: `188BD557-48FE-460E-8728-BD987112E7D0`
- Result: permission blocker is cleared; real approval instance creation is now working in GitHub Actions.
- Next: poll instance status and sync projected fields back into Feishu Base / monitor records.
```

- [ ] **Step 2: Write the comment body to a temp file**

Run:

```bash
cat > /tmp/pr7-feishu-approval-success.md <<'EOF'
UPDATED: Feishu approval real smoke succeeded

- Scope status: `approval:approval` and `approval:instance` are now enabled and verified live.
- Smoke run: https://github.com/yunya1991/DREAM-AGENT/actions/runs/27098459714
- Approval code: `6DE5C07A-5FDC-44D0-9110-8B74AB0837B6`
- Applicant open_id path: confirmed request body must use `open_id`, not `user_id`
- Created instance: `188BD557-48FE-460E-8728-BD987112E7D0`
- Result: permission blocker is cleared; real approval instance creation is now working in GitHub Actions.
- Next: poll instance status and sync projected fields back into Feishu Base / monitor records.
EOF
```

Expected: file exists at `/tmp/pr7-feishu-approval-success.md`

- [ ] **Step 3: Post the comment to PR #7**

Run:

```bash
gh pr comment 7 --body-file /tmp/pr7-feishu-approval-success.md
```

Expected: GitHub returns the new comment URL.

- [ ] **Step 4: Verify the comment landed**

Run:

```bash
gh pr view 7 --comments --json comments --jq '.comments[-1] | {url: .url, body: .body}'
```

Expected: output includes `Feishu approval real smoke succeeded`

- [ ] **Step 5: Commit**

```bash
# No repo file changes in this task. Do not create a git commit.
true
```

## Task 2: Add Approval Polling Projection Contract

**Files:**
- Create: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`
- Modify: `github-actions/feishu_approval_api.py`
- Create: `github-actions/poll_feishu_approval_and_sync_base.py`

- [ ] **Step 1: Write the failing test for approved-instance projection**

```python
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLL = load_module(
    "poll_feishu_approval_and_sync_base",
    "github-actions/poll_feishu_approval_and_sync_base.py",
)


class PollFeishuApprovalSyncBaseTest(unittest.TestCase):
    @patch.object(POLL.APPROVAL_API, "get_instance")
    @patch.object(POLL, "upsert_base_record")
    def test_approved_instance_projects_task_goal_and_writeback(
        self,
        mock_upsert,
        mock_get_instance,
    ):
        mock_get_instance.return_value = {"status": "APPROVED"}
        mock_upsert.side_effect = [
            {"record_id": "rec_task_written"},
            {"record_id": "rec_goal_written"},
        ]

        result = POLL.poll_and_sync(
            {
                "tenant_access_token": "tenant-token",
                "approval_instance_code": "instance-1",
                "task_payload": {
                    "task_id": "task-1",
                    "task_name": "Smoke",
                    "goal_id": "goal-1",
                    "approval_instance_code": "instance-1",
                    "approval_decision_id": "task-1",
                    "approval_status": "pending",
                    "automation_status": "paused",
                },
                "goal_payload": {
                    "goal_id": "goal-1",
                    "goal_name": "Goal",
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
            }
        )

        self.assertEqual(result["task_updates"]["approval_status"], "approved")
        self.assertEqual(result["task_updates"]["automation_status"], "running")
        self.assertEqual(result["goal_record"]["goal_status"], "active")
        self.assertEqual(mock_upsert.call_count, 2)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: FAIL because `poll_feishu_approval_and_sync_base.py` does not exist yet.

- [ ] **Step 3: Write minimal reusable projection helpers**

Add this helper to `github-actions/feishu_approval_api.py`:

```python
def build_status_projection(instance, decision_id, instance_code):
    resolved = resolve_instance_status(instance, decision_id)
    resolved["approval_instance_code"] = instance_code
    return resolved
```

Create `github-actions/poll_feishu_approval_and_sync_base.py` with:

```python
import json
import sys
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module(name, file_name):
    path = HERE / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SYNC = load_module("sync_github_to_feishu", "sync_github_to_feishu.py")
GOAL = load_module("build_goal_progress_record", "build_goal_progress_record.py")
APPROVAL_API = load_module("feishu_approval_api", "feishu_approval_api.py")
LARK = load_module("lark_cli", "lark_cli.py")


def upsert_base_record(base_token, table_id, record_id, fields):
    payload = [
        "base",
        "+record-upsert",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--record-id",
        record_id,
        "--json",
        json.dumps(fields, ensure_ascii=False),
    ]
    return LARK.run_lark_json(payload, identity="bot")


def poll_and_sync(payload):
    base_sync = payload["base_sync"]
    task_updates = dict(payload["task_payload"])
    instance_code = payload["approval_instance_code"]
    instance = APPROVAL_API.get_instance(payload["tenant_access_token"], instance_code)
    task_updates.update(
        APPROVAL_API.build_status_projection(
            instance,
            decision_id=task_updates.get("approval_decision_id", task_updates["task_id"]),
            instance_code=instance_code,
        )
    )
    task_record = SYNC.build_feishu_record(task_updates)
    goal_record = GOAL.build_goal_record(payload["goal_payload"], [task_updates, *payload["sibling_tasks"]])
    upsert_base_record(
        base_sync["base_token"],
        base_sync["task_table_id"],
        base_sync["task_record_id"],
        task_record,
    )
    upsert_base_record(
        base_sync["base_token"],
        base_sync["goal_table_id"],
        base_sync["goal_record_id"],
        goal_record,
    )
    return {
        "task_updates": task_updates,
        "task_record": task_record,
        "goal_record": goal_record,
    }


if __name__ == "__main__":
    json.dump(poll_and_sync(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the new test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_approval_api.py \
        github-actions/poll_feishu_approval_and_sync_base.py \
        github-actions/tests/test_poll_feishu_approval_and_sync_base.py
git commit -m "feat: add approval poll and base sync"
```

## Task 3: Verify Base Writeback Against the Real Tables

**Files:**
- Modify: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`

- [ ] **Step 1: Add a failing test that locks the exact Base write payload**

```python
    @patch.object(POLL.APPROVAL_API, "get_instance")
    @patch.object(POLL, "upsert_base_record")
    def test_writeback_uses_feishu_monitor_fields(self, mock_upsert, mock_get_instance):
        mock_get_instance.return_value = {"status": "REJECTED"}
        mock_upsert.side_effect = [{"record_id": "rec_task"}, {"record_id": "rec_goal"}]

        POLL.poll_and_sync(
            {
                "tenant_access_token": "tenant-token",
                "approval_instance_code": "instance-2",
                "task_payload": {
                    "task_id": "task-2",
                    "task_name": "Smoke 2",
                    "goal_id": "goal-2",
                    "approval_instance_code": "instance-2",
                    "approval_decision_id": "task-2",
                },
                "goal_payload": {"goal_id": "goal-2", "goal_name": "Goal 2", "goal_owner": "owner"},
                "sibling_tasks": [],
                "base_sync": {
                    "base_token": "app_base",
                    "task_table_id": "tbl_task",
                    "task_record_id": "rec_task",
                    "goal_table_id": "tbl_goal",
                    "goal_record_id": "rec_goal",
                },
            }
        )

        task_fields = mock_upsert.call_args_list[0].args[3]
        self.assertEqual(task_fields["审批状态"], "rejected")
        self.assertEqual(task_fields["审批决策ID"], "task-2")
        self.assertEqual(task_fields["任务ID"], "task-2")
```

- [ ] **Step 2: Run the test to verify it fails if field mapping regresses**

Run:

```bash
python3 -m unittest github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: FAIL if the record mapping is incomplete.

- [ ] **Step 3: Fill in any missing defaults in the poller**

Update `poll_feishu_approval_and_sync_base.py` so `task_updates` always keeps these fields before projection:

```python
    task_updates.setdefault("approval_status", "pending")
    task_updates.setdefault("approval_decision_id", task_updates.get("task_id", ""))
    task_updates.setdefault("automation_status", "paused")
    task_updates.setdefault("approval_instance_code", instance_code)
```

- [ ] **Step 4: Run the targeted tests and a focused regression bundle**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_run_goal_progress_approval_cycle.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add github-actions/poll_feishu_approval_and_sync_base.py \
        github-actions/tests/test_poll_feishu_approval_and_sync_base.py
git commit -m "feat: project approval status into feishu monitor records"
```

## Task 4: Silence Node 20 Workflow Warnings

**Files:**
- Modify: `.github/workflows/collab-acceptance-agent.yml`
- Modify: `.github/workflows/collab-validator-agent.yml`
- Modify: `github-actions/tests/test_collab_workflows_present.py`

- [ ] **Step 1: Write the failing workflow contract test**

Add this test to `github-actions/tests/test_collab_workflows_present.py`:

```python
    def test_collab_workflows_force_node24_for_deprecated_js_actions(self):
        acceptance = (
            REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        validator = (
            REPO_ROOT / ".github" / "workflows" / "collab-validator-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true", acceptance)
        self.assertIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true", validator)
```

- [ ] **Step 2: Run the workflow contract test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_collab_workflows_present.py -v
```

Expected: FAIL because the new env key is missing.

- [ ] **Step 3: Add the Node 24 override to both workflows**

Add this top-level env block to each workflow file if it is not already present:

```yaml
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
```

- [ ] **Step 4: Run the workflow contract test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_collab_workflows_present.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/collab-acceptance-agent.yml \
        .github/workflows/collab-validator-agent.yml \
        github-actions/tests/test_collab_workflows_present.py
git commit -m "ci: force node24 for collab workflows"
```

## Task 5: Update Repo Docs and Local Skill Notes

**Files:**
- Modify: `README.md`
- Modify: `docs/04-ENGINEERING-INDEX.md`
- Modify: `docs/06-SKILLS-INVENTORY.md`
- Modify: `/Users/zhangjiangtao/.trae/skills/lark-approval/SKILL.md`

- [ ] **Step 1: Write the exact doc snippets before editing**

Add this summary block to repo docs:

```markdown
### Feishu Approval Real Smoke Status

- Required scopes verified live: `approval:approval`, `approval:instance`
- Successful smoke run: `27098459714`
- Real instance code: `188BD557-48FE-460E-8728-BD987112E7D0`
- Request body pitfalls:
  - `form` must be `json.dumps([...])`, not a raw array
  - applicant `open_id` must go in `open_id`, not `user_id`
- Workflow runtime note: collab workflows force Node 24 for deprecated JavaScript actions
```

Add this local skill checklist block:

```markdown
## Real Smoke Checklist

- Before creating an instance, verify app scopes `approval:approval` and `approval:instance`.
- For instance creation, send applicant identity in `open_id` when you already have an `ou_...` value.
- Serialize `form` as a JSON string, for example `json.dumps([])`.
- If GitHub Actions smoke succeeds, record the run URL and `instance_code` back into project docs / PR comments.
```

- [ ] **Step 2: Apply the doc edits**

Use the prepared blocks to update:

```text
README.md
docs/04-ENGINEERING-INDEX.md
docs/06-SKILLS-INVENTORY.md
/Users/zhangjiangtao/.trae/skills/lark-approval/SKILL.md
```

Expected: all four files mention the real smoke result and key pitfalls without introducing unrelated refactors.

- [ ] **Step 3: Run focused verification**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
  github-actions/tests/test_collab_workflows_present.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add README.md \
        docs/04-ENGINEERING-INDEX.md \
        docs/06-SKILLS-INVENTORY.md \
        /Users/zhangjiangtao/.trae/skills/lark-approval/SKILL.md
git commit -m "docs: record feishu approval smoke closure"
```

- [ ] **Step 5: Push and final verification**

Run:

```bash
git push origin pilot/acceptance-orchestration-v2-e2e-20260607
gh workflow run collab-acceptance-agent.yml \
  --ref pilot/acceptance-orchestration-v2-e2e-20260607 \
  -f pr_number=7 \
  -f smoke_action=approval-smoke \
  -f approval_code=6DE5C07A-5FDC-44D0-9110-8B74AB0837B6 \
  -f applicant_open_id=ou_e4188db561199adccd1ba20636f9930a
```

Expected: push succeeds and the smoke workflow can still create a real approval instance.

## Self-Review

- Spec coverage:
  - PR 留痕：Task 1
  - 审批回读 + Base 回写：Task 2-3
  - Node 24 告警处理：Task 4
  - Skill / 仓库文档更新：Task 5
- Placeholder scan:
  - No `TODO` / `TBD`
  - Every code-bearing step includes concrete code or commands
- Type consistency:
  - Poller inputs standardize on `approval_instance_code`, `task_payload`, `goal_payload`, `sibling_tasks`, `base_sync`
  - Applicant identity continues to use `open_id` in the workflow, while the poller only uses the created `instance_code`

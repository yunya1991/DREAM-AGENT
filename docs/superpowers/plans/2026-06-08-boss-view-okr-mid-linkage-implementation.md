# Boss View and OKR Mid-Linkage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chinese boss-facing goal view in Feishu Base, add OKR linkage anchor fields plus workflow signals to the goal record payload, and bootstrap the first three reminder workflows without turning Base into the source of truth.

**Architecture:** Reuse the existing `build_goal_progress_record.py` and approval/Base poller so the new boss view remains compatible with current sync entrypoints. Apply the Base schema and views directly in the real table, but generate workflow definitions through a small Python bootstrapper that resolves field IDs dynamically, so workflow creation stays repeatable and does not hardcode volatile IDs.

**Tech Stack:** Python 3, `unittest`, `lark-cli base +field-create/+view-create/+workflow-create`, Feishu Base, existing `github-actions` sync scripts

---

## File Map

- Modify: `github-actions/build_goal_progress_record.py`
  - Expand the goal record payload to emit both the existing English anchor fields and the new Chinese boss-view / OKR / workflow signal fields.
- Modify: `github-actions/poll_feishu_approval_and_sync_base.py`
  - Keep the goal-table writeback path aligned with the new goal record payload.
- Modify: `github-actions/tests/test_build_goal_progress_record.py`
  - Lock the new Chinese fields, OKR alignment state, and workflow signal behavior.
- Modify: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`
  - Verify the poller writes the expanded goal payload without regressing the existing approval projection.
- Create: `github-actions/bootstrap_goal_progress_workflows.py`
  - Resolve field IDs by name and generate the three workflow JSON bodies needed by the real Base.
- Create: `github-actions/tests/test_bootstrap_goal_progress_workflows.py`
  - Lock the workflow JSON contract so workflow creation remains reproducible.
- Modify online Base schema: real Base `SjCHbDasHarEcFsJjXwc5JZgnUr`, table `tblYwbyMwnO8j8iG`
  - Add Chinese boss fields, OKR anchor fields, owner user fields, and workflow signal fields.
- Modify online Base views: real Base `SjCHbDasHarEcFsJjXwc5JZgnUr`, table `tblYwbyMwnO8j8iG`
  - Create `老板视图（状态与阻塞）`, then set visible field order and sorting.
- Create online workflows in the same Base
  - `阻塞升级提醒`
  - `审批完成提醒更新目标`
  - `OKR对齐缺失提醒`

## Execution Guardrails

- Ignore the unrelated deletion `.github/workflows/feishu-approval-smoke.yml`; do not restore or stage it.
- Ignore `.superpowers/` files created during brainstorming; do not stage them.
- Prefer `--as user` for Base changes so the real table and workflows land in the visible user-owned workspace.
- Keep workflow automation in `disabled` state until JSON is verified, then enable intentionally.

## Task 1: Expand Goal Payload for Boss View and OKR Anchors

**Files:**
- Modify: `github-actions/build_goal_progress_record.py`
- Modify: `github-actions/tests/test_build_goal_progress_record.py`

- [ ] **Step 1: Write the failing tests for Chinese boss fields and OKR alignment**

Add these tests to `github-actions/tests/test_build_goal_progress_record.py`:

```python
    def test_build_goal_record_emits_chinese_boss_fields(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {
                "goal_id": "goal-boss-001",
                "goal_name": "中台前端对齐",
                "goal_owner": "governance-agent",
                "current_phase": "approval-sync",
                "next_milestone": "补齐阻塞后推进联调",
            },
            [
                {
                    "task_id": "task-1",
                    "approval_status": "pending",
                    "platform_status": "checks_pending",
                    "governance_status": "review_required",
                    "blocker": "等待审批实例最终状态",
                    "decision_summary": "instance_created:188BD557-48FE-460E-8728-BD987112E7D0",
                }
            ],
        )
        self.assertEqual(record["目标名称"], "中台前端对齐")
        self.assertEqual(record["当前状态"], "等待决策")
        self.assertEqual(record["当前阻塞"], "等待审批实例最终状态")
        self.assertEqual(record["风险等级"], "high")
        self.assertEqual(record["下一步动作"], "补齐阻塞后推进联调")
        self.assertEqual(record["最近决策摘要"], "instance_created:188BD557-48FE-460E-8728-BD987112E7D0")

    def test_goal_record_marks_missing_okr_alignment_for_active_goal(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {
                "goal_id": "goal-okr-001",
                "goal_name": "老板视图联动",
                "goal_status": "active",
                "next_milestone": "绑定 Objective",
            },
            [
                {
                    "task_id": "task-1",
                    "approval_status": "not_required",
                    "platform_status": "checks_green",
                    "governance_status": "ready",
                }
            ],
        )
        self.assertEqual(record["OKR对齐"], "待补OKR")
        self.assertEqual(record["workflow_signal"], "missing_okr_alignment")
```

- [ ] **Step 2: Run the focused test file and verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_goal_progress_record.py -v
```

Expected: FAIL with missing keys such as `目标名称`, `OKR对齐`, or `workflow_signal`.

- [ ] **Step 3: Implement minimal helper functions and expand the goal payload**

Update `github-actions/build_goal_progress_record.py` to add the helpers and payload keys below:

```python
STATUS_TO_CN = {
    "planned": "待开始",
    "active": "推进中",
    "blocked": "已阻塞",
    "waiting_decision": "等待决策",
    "ready_for_release": "待发布",
    "released": "已发布",
}


def to_boss_status(status):
    return STATUS_TO_CN.get(status, status or "待开始")


def compute_okr_alignment(goal, goal_status):
    if goal.get("okr_sync_status") in {"error", "failed"}:
        return "对齐异常"
    if goal.get("okr_objective_id"):
        return "已对齐"
    if goal_status in {"active", "blocked", "waiting_decision"}:
        return "待补OKR"
    return "待同步"


def compute_workflow_signal(tasks, okr_alignment):
    if any(task.get("approval_status") in {"pending", "timeout"} for task in tasks):
        return "approval_waiting"
    if okr_alignment != "已对齐":
        return "missing_okr_alignment"
    if any(task.get("risk_level") == "high" and task.get("blocker") for task in tasks):
        return "risk_blocked"
    return "healthy"


def build_goal_record(goal, tasks):
    goal_status = compute_goal_status(tasks)
    blocker = first_non_empty(tasks, "blocker")
    decision_summary = first_non_empty(tasks, "decision_summary")
    risk = choose_risk(tasks)
    okr_alignment = compute_okr_alignment(goal, goal_status)
    next_action = goal.get("next_action") or goal.get("next_milestone", "")
    return {
        "goal_id": goal.get("goal_id", ""),
        "goal_name": goal.get("goal_name", ""),
        "goal_owner": goal.get("goal_owner", ""),
        "goal_status": goal_status,
        "goal_progress": compute_goal_progress(tasks),
        "current_phase": goal.get("current_phase", ""),
        "key_blocker": blocker,
        "next_milestone": goal.get("next_milestone", ""),
        "risk_level": risk,
        "latest_decision_summary": decision_summary,
        "目标名称": goal.get("goal_name", ""),
        "当前状态": to_boss_status(goal_status),
        "当前阻塞": blocker,
        "风险等级": risk,
        "下一步动作": next_action,
        "最近决策摘要": decision_summary,
        "OKR对齐": okr_alignment,
        "okr_objective_id": goal.get("okr_objective_id", ""),
        "okr_objective_title": goal.get("okr_objective_title", ""),
        "okr_owner": goal.get("okr_owner", ""),
        "okr_sync_status": goal.get("okr_sync_status", ""),
        "okr_last_sync_at": goal.get("okr_last_sync_at", ""),
        "workflow_signal": compute_workflow_signal(tasks, okr_alignment),
        "last_workflow_run_at": goal.get("last_workflow_run_at", ""),
    }
```

- [ ] **Step 4: Run the focused tests and the poller regression bundle**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_goal_progress_record.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: the new build-goal tests PASS; the poller test may still fail until Task 2 updates it.

- [ ] **Step 5: Commit**

```bash
git add github-actions/build_goal_progress_record.py \
        github-actions/tests/test_build_goal_progress_record.py
git commit -m "feat: add boss view fields to goal payload"
```

## Task 2: Keep the Approval Poller Compatible with the Expanded Goal Payload

**Files:**
- Modify: `github-actions/poll_feishu_approval_and_sync_base.py`
- Modify: `github-actions/tests/test_poll_feishu_approval_and_sync_base.py`

- [ ] **Step 1: Add a failing poller assertion for the new goal fields**

Extend `github-actions/tests/test_poll_feishu_approval_and_sync_base.py` with:

```python
    @patch.object(POLL.APPROVAL_API, "get_instance")
    @patch.object(POLL, "upsert_base_record")
    def test_goal_writeback_contains_boss_view_fields(self, mock_upsert, mock_get_instance):
        mock_get_instance.return_value = {"status": "APPROVED"}
        mock_upsert.side_effect = [{"record_id": "rec_task"}, {"record_id": "rec_goal"}]

        result = POLL.poll_and_sync(
            {
                "tenant_access_token": "tenant-token",
                "approval_instance_code": "instance-3",
                "task_payload": {
                    "task_id": "task-3",
                    "task_name": "Boss View",
                    "goal_id": "goal-3",
                    "approval_decision_id": "task-3",
                    "blocker": "等待老板确认",
                    "decision_summary": "approved_and_resume",
                },
                "goal_payload": {
                    "goal_id": "goal-3",
                    "goal_name": "老板视图联动",
                    "goal_owner": "governance-agent",
                    "next_milestone": "创建 workflow",
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

        self.assertEqual(result["goal_record"]["目标名称"], "老板视图联动")
        self.assertEqual(result["goal_record"]["OKR对齐"], "待补OKR")
        self.assertIn("workflow_signal", result["goal_record"])
```

- [ ] **Step 2: Run the target poller test and verify it fails if the payload is incomplete**

Run:

```bash
python3 -m unittest github-actions/tests/test_poll_feishu_approval_and_sync_base.py -v
```

Expected: FAIL if the expanded goal payload is not flowing through.

- [ ] **Step 3: Keep the poller input contract explicit**

Ensure `github-actions/poll_feishu_approval_and_sync_base.py` still passes the full goal payload untouched to `build_goal_record()`:

```python
    goal_record = GOAL.build_goal_record(
        payload["goal_payload"],
        [task_updates, *payload["sibling_tasks"]],
    )
```

No field filtering should be added in the poller; the builder owns the goal payload shape.

- [ ] **Step 4: Run the approval regression bundle**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_goal_progress_record.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
  github-actions/tests/test_run_goal_progress_approval_cycle.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add github-actions/poll_feishu_approval_and_sync_base.py \
        github-actions/tests/test_poll_feishu_approval_and_sync_base.py
git commit -m "test: lock boss view goal writeback payload"
```

## Task 3: Add Real Base Fields and Create the Chinese Boss View

**Files:**
- Real Base: `SjCHbDasHarEcFsJjXwc5JZgnUr`
- Real table: `tblYwbyMwnO8j8iG`

- [ ] **Step 1: Inspect the current table structure before writing**

Run:

```bash
lark-cli base +table-get \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --as user --format json
```

Expected: output includes current fields and the existing views `默认总览（先看这里）` and `阻塞与下一步`.

- [ ] **Step 2: Create the Chinese boss fields and owner/user anchor fields**

Run these commands one by one:

```bash
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"目标名称","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"当前状态","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"当前阻塞","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"风险等级","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"下一步动作","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"最近决策摘要","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"OKR对齐","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"目标负责人","type":"user","multiple":false}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"OKR负责人","type":"user","multiple":false}' --as user --format json
```

Expected: each command returns `{ "created": true }` for the new field.

- [ ] **Step 3: Create OKR anchor and workflow signal fields**

Run:

```bash
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"okr_objective_id","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"okr_objective_title","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"okr_owner","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"okr_sync_status","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"okr_last_sync_at","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"workflow_signal","type":"text"}' --as user --format json
lark-cli base +field-create --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --table-id tblYwbyMwnO8j8iG --json '{"name":"last_workflow_run_at","type":"text"}' --as user --format json
```

- [ ] **Step 4: Create and configure the boss view**

Run:

```bash
lark-cli base +view-create \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --json '{"name":"老板视图（状态与阻塞）","type":"grid"}' \
  --as user --format json

lark-cli base +view-set-visible-fields \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --view-id '老板视图（状态与阻塞）' \
  --json '{"visible_fields":["goal_id","目标名称","当前状态","当前阻塞","风险等级","下一步动作","OKR对齐","最近决策摘要"]}' \
  --as user --format json

lark-cli base +view-set-sort \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --view-id '老板视图（状态与阻塞）' \
  --json '{"sort_config":[{"field":"风险等级","desc":true},{"field":"当前状态","desc":false}]}' \
  --as user --format json
```

Expected: the new view exists and the visible field order matches the boss-view design.

- [ ] **Step 5: Backfill the existing record with the new fields**

Run:

```bash
python3 - <<'PY'
import importlib.util
import json
from pathlib import Path

path = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/build_goal_progress_record.py")
spec = importlib.util.spec_from_file_location("goal_builder", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

payload = module.build_goal_record(
    {
        "goal_id": "goal-feishu-approval",
        "goal_name": "Feishu approval closure",
        "goal_owner": "governance-agent",
        "current_phase": "approval-sync",
        "next_milestone": "approve_or_reject_instance_then_sync_final_status",
    },
    [
        {
            "task_id": "task-feishu-approval-smoke-001",
            "approval_status": "pending",
            "platform_status": "checks_pending",
            "governance_status": "review_required",
            "blocker": "local_user_missing_scope:approval:instance:read",
            "decision_summary": "instance_created:188BD557-48FE-460E-8728-BD987112E7D0",
        }
    ],
)

with open("/tmp/goal-boss-backfill.json", "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False)

print("/tmp/goal-boss-backfill.json")
PY

lark-cli base +record-upsert \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --record-id recvlSzwI4UB8M \
  --json "$(cat /tmp/goal-boss-backfill.json)" \
  --as user --format json
```

Expected: the existing goal row shows the new Chinese fields in the boss view.

## Task 4: Generate Workflow Definitions with Code Instead of Hardcoded Field IDs

**Files:**
- Create: `github-actions/bootstrap_goal_progress_workflows.py`
- Create: `github-actions/tests/test_bootstrap_goal_progress_workflows.py`

- [ ] **Step 1: Write the failing workflow bootstrap tests**

Create `github-actions/tests/test_bootstrap_goal_progress_workflows.py` with:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_goal_progress_workflows",
    ROOT / "github-actions" / "bootstrap_goal_progress_workflows.py",
)
MODULE = importlib.util.module_from_spec(SPEC)


class BootstrapGoalProgressWorkflowsTests(unittest.TestCase):
    def test_builds_three_workflow_specs(self):
        SPEC.loader.exec_module(MODULE)
        fields = {
            "当前阻塞": "fld_blocker",
            "风险等级": "fld_risk",
            "approval_status": "fld_approval",
            "OKR对齐": "fld_okr_align",
            "目标负责人": "fld_goal_owner_user",
            "OKR负责人": "fld_okr_owner_user",
        }
        workflows = MODULE.build_workflow_specs(table_name="目标推进表", field_ids=fields)
        self.assertEqual(len(workflows), 3)
        self.assertEqual(workflows[0]["title"], "阻塞升级提醒")
        self.assertEqual(workflows[1]["title"], "审批完成提醒更新目标")
        self.assertEqual(workflows[2]["title"], "OKR对齐缺失提醒")

    def test_missing_fields_raise_clear_error(self):
        SPEC.loader.exec_module(MODULE)
        with self.assertRaisesRegex(ValueError, "missing workflow fields"):
            MODULE.build_workflow_specs(table_name="目标推进表", field_ids={"当前阻塞": "fld_only"})
```

- [ ] **Step 2: Run the workflow bootstrap test and verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_bootstrap_goal_progress_workflows.py -v
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement the workflow bootstrapper**

Create `github-actions/bootstrap_goal_progress_workflows.py` with:

```python
import json
import sys
import time


REQUIRED_FIELDS = [
    "当前阻塞",
    "风险等级",
    "approval_status",
    "OKR对齐",
    "目标负责人",
    "OKR负责人",
]


def require_fields(field_ids):
    missing = [name for name in REQUIRED_FIELDS if name not in field_ids]
    if missing:
        raise ValueError(f"missing workflow fields: {', '.join(missing)}")


def build_workflow_specs(table_name, field_ids):
    require_fields(field_ids)
    blocker_ref = f"$.trigger_blocker.{field_ids['目标负责人']}"
    okr_owner_ref = f"$.trigger_blocker.{field_ids['OKR负责人']}"
    return [
        {
            "client_token": f"goal-blocker-{int(time.time())}",
            "title": "阻塞升级提醒",
            "steps": [
                {
                    "id": "trigger_blocker",
                    "type": "ChangeRecordTrigger",
                    "title": "监控高风险阻塞",
                    "next": "notify_goal_owner",
                    "data": {"table_name": table_name},
                },
                {
                    "id": "notify_goal_owner",
                    "type": "LarkMessageAction",
                    "title": "提醒目标负责人",
                    "next": None,
                    "data": {
                        "receiver": [{"value_type": "ref", "value": blocker_ref}],
                        "send_to_everyone": False,
                        "title": [{"value_type": "text", "value": "目标阻塞升级提醒"}],
                        "content": [{"value_type": "text", "value": "当前目标存在高风险阻塞，请更新目标推进表。"}],
                        "btn_list": [],
                    },
                },
            ],
        },
        {
            "client_token": f"goal-approval-{int(time.time())+1}",
            "title": "审批完成提醒更新目标",
            "steps": [
                {
                    "id": "trigger_approval",
                    "type": "ChangeRecordTrigger",
                    "title": "监控审批状态终态",
                    "next": "notify_after_approval",
                    "data": {"table_name": table_name},
                },
                {
                    "id": "notify_after_approval",
                    "type": "LarkMessageAction",
                    "title": "提醒更新目标状态",
                    "next": None,
                    "data": {
                        "receiver": [{"value_type": "ref", "value": blocker_ref}],
                        "send_to_everyone": False,
                        "title": [{"value_type": "text", "value": "审批完成，请更新目标"}],
                        "content": [{"value_type": "text", "value": "审批状态已变化，请同步当前状态、下一步动作与 OKR 对齐。"}],
                        "btn_list": [],
                    },
                },
            ],
        },
        {
            "client_token": f"goal-okr-{int(time.time())+2}",
            "title": "OKR对齐缺失提醒",
            "steps": [
                {
                    "id": "trigger_okr",
                    "type": "ChangeRecordTrigger",
                    "title": "监控 OKR 对齐缺失",
                    "next": "notify_okr_owner",
                    "data": {"table_name": table_name},
                },
                {
                    "id": "notify_okr_owner",
                    "type": "LarkMessageAction",
                    "title": "提醒补齐 OKR",
                    "next": None,
                    "data": {
                        "receiver": [{"value_type": "ref", "value": okr_owner_ref}],
                        "send_to_everyone": False,
                        "title": [{"value_type": "text", "value": "目标尚未完成 OKR 对齐"}],
                        "content": [{"value_type": "text", "value": "该目标已进入推进中，但仍未完成 OKR 对齐，请补齐 Objective 或说明异常。"}],
                        "btn_list": [],
                    },
                },
            ],
        },
    ]


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_workflow_specs(payload["table_name"], payload["field_ids"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the workflow bootstrap tests**

Run:

```bash
python3 -m unittest github-actions/tests/test_bootstrap_goal_progress_workflows.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add github-actions/bootstrap_goal_progress_workflows.py \
        github-actions/tests/test_bootstrap_goal_progress_workflows.py
git commit -m "feat: add goal progress workflow bootstrapper"
```

## Task 5: Create and Enable the Three Real Base Workflows

**Files:**
- Real Base: `SjCHbDasHarEcFsJjXwc5JZgnUr`
- Real table: `tblYwbyMwnO8j8iG`

- [ ] **Step 1: Read the live field structure and capture the required field IDs**

Run:

```bash
lark-cli base +field-list \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --offset 0 --limit 100 \
  --as user --format json
```

Expected: output includes IDs for `当前阻塞`, `风险等级`, `approval_status`, `OKR对齐`, `目标负责人`, and `OKR负责人`.

- [ ] **Step 2: Generate workflow JSON from the bootstrapper**

Run:

```bash
python3 - <<'PY'
import json
import subprocess

field_data = json.loads(subprocess.check_output([
    "lark-cli", "base", "+field-list",
    "--base-token", "SjCHbDasHarEcFsJjXwc5JZgnUr",
    "--table-id", "tblYwbyMwnO8j8iG",
    "--offset", "0",
    "--limit", "100",
    "--as", "user",
    "--format", "json",
], text=True))

field_ids = {item["name"]: item["id"] for item in field_data["data"]["items"]}
payload = {"table_name": "目标推进表", "field_ids": field_ids}

with open("/tmp/goal-workflows.json", "w", encoding="utf-8") as fh:
    subprocess.run(
        ["python3", "github-actions/bootstrap_goal_progress_workflows.py"],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        check=True,
        stdout=fh,
    )

print("/tmp/goal-workflows.json")
PY
```

Expected: `/tmp/goal-workflows.json` exists and contains three workflow JSON objects.

- [ ] **Step 3: Create the workflows in Base**

Run the three create commands using the generated JSON objects:

```bash
python3 - <<'PY'
import json
import subprocess

workflows = json.load(open("/tmp/goal-workflows.json", encoding="utf-8"))
for wf in workflows:
    subprocess.run([
        "lark-cli", "base", "+workflow-create",
        "--base-token", "SjCHbDasHarEcFsJjXwc5JZgnUr",
        "--json", json.dumps(wf, ensure_ascii=False),
        "--as", "user",
        "--format", "json",
    ], check=True)
PY
```

Expected: three `workflow_id` values are returned, each in `disabled` status.

- [ ] **Step 4: Enable the workflows after verifying titles**

Run:

```bash
lark-cli base +workflow-list --base-token SjCHbDasHarEcFsJjXwc5JZgnUr --as user --format json
```

Then enable the three workflows by title:

```bash
python3 - <<'PY'
import json
import subprocess

result = json.loads(subprocess.check_output([
    "lark-cli", "base", "+workflow-list",
    "--base-token", "SjCHbDasHarEcFsJjXwc5JZgnUr",
    "--as", "user",
    "--format", "json",
], text=True))

targets = {
    "阻塞升级提醒",
    "审批完成提醒更新目标",
    "OKR对齐缺失提醒",
}

for item in result["data"]["items"]:
    if item["title"] in targets:
        subprocess.run([
            "lark-cli", "base", "+workflow-enable",
            "--base-token", "SjCHbDasHarEcFsJjXwc5JZgnUr",
            "--workflow-id", item["workflow_id"],
            "--as", "user",
            "--format", "json",
        ], check=True)
PY
```

Expected: each command returns a workflow status of `enabled`.

- [ ] **Step 5: Verify the final surface**

Run:

```bash
lark-cli base +view-list \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --offset 0 --limit 20 \
  --as user --format json

lark-cli base +record-get \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --record-id recvlSzwI4UB8M \
  --as user --format json
```

Expected:

- the view list includes `老板视图（状态与阻塞）`
- the goal record includes `目标名称`, `当前状态`, `当前阻塞`, `风险等级`, `下一步动作`, `OKR对齐`, `最近决策摘要`

## Self-Review

- Spec coverage:
  - 中文老板视图：Task 1-3
  - `目标推进表 ↔ OKR` 锚点与中文枚举：Task 1-3
  - 首批三条 workflow：Task 4-5
  - dashboard 暂不实施：由任务范围和 File Map 明确排除
- Placeholder scan:
  - No `TODO` / `TBD`
  - Every code step includes concrete code
  - Every Base step includes exact CLI commands
- Type consistency:
  - Goal payload keeps English anchors and adds Chinese display keys
  - `OKR对齐` is always Chinese enum text, not raw IDs
  - `workflow_signal` stays a text field and is generated in one place: `build_goal_record()`

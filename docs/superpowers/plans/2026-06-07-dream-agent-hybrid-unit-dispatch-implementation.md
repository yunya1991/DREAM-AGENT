---
id: DREAM-AGENT-HYBRID-UNIT-DISPATCH-IMPLEMENTATION
type: plan
owner: governance-agent
depends:
  - DREAM-AGENT-HYBRID-UNIT-DISPATCH-DESIGN
version: 1
last_verified: 2026-06-07
---

# Dream-Agent Hybrid Unit Dispatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `DREAM-AGENT` 落地 `Hybrid Unit Dispatch` 最小可执行闭环，支持混合单元建模、GitHub 主链调度、飞书协作资产模式、版本锚点与回滚记录，并提供首个“策略设置成功 -> 生成策略任务单”样板单元。

**Architecture:** 先把混合单元与回滚字段并入现有 ledger 真源，再新增一套独立的 payload builder / checker / runner，避免污染已有 collaboration v1 协议；随后用新的 workflow_dispatch 工作流把 dispatch -> validator -> governance 这一条最小主链跑通，并把飞书能力作为正式字段纳入调度结果，但允许走 `degraded-with-backfill`。最后补齐文档入口与样板数据，让后续 agent 可以直接复制样板单元扩展策略主线。

**Tech Stack:** Markdown, JSON, Python 3 standard library, unittest, GitHub Actions YAML, existing ledger/tasks structure, existing `github-actions` orchestration scripts, existing comment template conventions.

---

## Repository Layout Changes

**Create**
- `ledger/templates/hybrid-unit-record.json`
- `github-actions/build_hybrid_unit_dispatch_payload.py`
- `github-actions/check_hybrid_unit_dispatch.py`
- `github-actions/run_hybrid_unit_dispatch.py`
- `github-actions/tests/test_build_hybrid_unit_dispatch_payload.py`
- `github-actions/tests/test_check_hybrid_unit_dispatch.py`
- `github-actions/tests/test_run_hybrid_unit_dispatch.py`
- `.github/workflows/collab-hybrid-unit-dispatch.yml`
- `templates/pr-comment-hybrid-unit-dispatch.md`
- `templates/pr-comment-rollback-decision.md`

**Modify**
- `ledger/templates/task-record.json`
- `ledger/tasks/index.json`
- `github-actions/update_agent_ledger.py`
- `github-actions/tests/test_update_agent_ledger.py`
- `docs/superpowers/templates/agent-task-card.md`
- `README.md`
- `docs/README.md`
- `docs/04-ENGINEERING-INDEX.md`
- `docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md`
- `docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md`

---

## Implementation Sequence

1. 先扩充 ledger 模型与模板，使混合单元、飞书资产模式、版本锚点、回滚策略都有真源字段
2. 再新增 dispatch payload builder 与规则 checker，保证单元在发车前就能被验证
3. 再新增 runner 和 workflow，把现有 GitHub 主链接成一条最小可跑流程
4. 再补 ledger updater、评论模板与回滚决策记录
5. 最后放入首个策略主线样板单元，并更新入口文档

---

### Task 1: 扩充 ledger 模型为混合单元真源

**Files:**
- Create: `ledger/templates/hybrid-unit-record.json`
- Modify: `ledger/templates/task-record.json`
- Modify: `ledger/tasks/index.json`
- Modify: `github-actions/tests/test_update_agent_ledger.py`

- [ ] **Step 1: 为混合单元模板添加失败测试**

Modify `github-actions/tests/test_update_agent_ledger.py` by appending:

```python
class HybridUnitTemplateTests(unittest.TestCase):
    def test_hybrid_unit_template_exposes_dispatch_and_rollback_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "hybrid-unit-record.json").read_text(
                encoding="utf-8"
            )
        )
        required = [
            "unit_id",
            "track",
            "frontend_surface",
            "platform_capability",
            "acceptance_target",
            "collaboration_asset_surface",
            "feishu_asset_mode",
            "version_anchor",
            "rollback_strategy",
        ]
        for key in required:
            self.assertIn(key, data)

    def test_task_template_includes_hybrid_dispatch_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "task-record.json").read_text(
                encoding="utf-8"
            )
        )
        for key in [
            "unit_id",
            "feishu_asset_mode",
            "version_anchor",
            "rollback_strategy",
        ]:
            self.assertIn(key, data)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_update_agent_ledger.py -v
```

Expected:

- FAIL because `ledger/templates/hybrid-unit-record.json` does not exist yet
- FAIL because `task-record.json` does not yet contain hybrid dispatch fields

- [ ] **Step 3: 新建混合单元模板并扩展任务模板**

Create `ledger/templates/hybrid-unit-record.json`:

```json
{
  "unit_id": "unit-strategy-task-ticket-001",
  "unit_name": "策略设置成功 -> 生成策略任务单",
  "track": "strategy-mainline",
  "goal": "把策略设置结果转换成可追踪任务单",
  "frontend_surface": {
    "route": "/ui-map",
    "entry": "strategy-status-card",
    "visible_state": "ticket-ready"
  },
  "platform_capability": {
    "service": "strategy-task-ticket-service",
    "input_contract": "strategy-setting-result",
    "output_contract": "strategy-task-ticket"
  },
  "execution_path": [
    "read strategy setting result",
    "create task ticket object",
    "persist ticket identifier",
    "emit acceptance-ready state"
  ],
  "acceptance_target": {
    "mode": "chain-runnable",
    "required_evidence": [
      "ticket_id",
      "ticket_status",
      "workflow_run_id"
    ]
  },
  "collaboration_asset_surface": {
    "base_record_required": true,
    "okr_link_required": false,
    "docs_sync_required": true
  },
  "feishu_asset_mode": "degraded-with-backfill",
  "dependencies": [],
  "suggested_agents": [
    "collab-developer-agent",
    "collab-validator-agent",
    "collab-governance-agent"
  ],
  "handoff_contract": {
    "required_outputs": [
      "ticket_id",
      "acceptance_request_id",
      "version_anchor"
    ]
  },
  "fallback_strategy": "GitHub-only with Feishu backfill",
  "version_anchor": {
    "git_commit_before": "",
    "git_branch_or_pr_ref": "",
    "workflow_run_id": "",
    "acceptance_request_id": "",
    "feishu_asset_before_snapshot": ""
  },
  "rollback_strategy": {
    "default_level": "unit",
    "trigger": [
      "validator_direction_error",
      "acceptance_chain_failed"
    ],
    "owner": "governance-agent"
  },
  "next_unit": "unit-strategy-ticket-execution-002"
}
```

Update `ledger/templates/task-record.json` by adding these fields near the existing governance fields:

```json
  "unit_id": "",
  "feishu_asset_mode": "full-sync",
  "version_anchor": {
    "git_commit_before": "",
    "git_branch_or_pr_ref": "",
    "workflow_run_id": "",
    "acceptance_request_id": "",
    "feishu_asset_before_snapshot": ""
  },
  "rollback_strategy": {
    "default_level": "unit",
    "trigger": [],
    "owner": ""
  },
```

Update the open sample task inside `ledger/tasks/index.json` to include:

```json
      "unit_id": "",
      "feishu_asset_mode": "full-sync",
      "version_anchor": {
        "git_commit_before": "",
        "git_branch_or_pr_ref": "",
        "workflow_run_id": "",
        "acceptance_request_id": "",
        "feishu_asset_before_snapshot": ""
      },
      "rollback_strategy": {
        "default_level": "unit",
        "trigger": [],
        "owner": ""
      },
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_update_agent_ledger.py -v
```

Expected:

- PASS for the new `HybridUnitTemplateTests`

- [ ] **Step 5: Commit**

```bash
git add ledger/templates/hybrid-unit-record.json ledger/templates/task-record.json ledger/tasks/index.json github-actions/tests/test_update_agent_ledger.py
git commit -m "feat: add hybrid unit ledger schema"
```

---

### Task 2: 新增 dispatch payload builder 与规则 checker

**Files:**
- Create: `github-actions/build_hybrid_unit_dispatch_payload.py`
- Create: `github-actions/check_hybrid_unit_dispatch.py`
- Create: `github-actions/tests/test_build_hybrid_unit_dispatch_payload.py`
- Create: `github-actions/tests/test_check_hybrid_unit_dispatch.py`

- [ ] **Step 1: 先写 builder 失败测试**

Create `github-actions/tests/test_build_hybrid_unit_dispatch_payload.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_hybrid_unit_dispatch_payload.py"
SPEC = importlib.util.spec_from_file_location("build_hybrid_unit_dispatch_payload", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildHybridUnitDispatchPayloadTests(unittest.TestCase):
    def test_build_payload_extracts_hybrid_dispatch_fields(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_payload(
            {
                "unit": {
                    "unit_id": "unit-001",
                    "track": "strategy-mainline",
                    "feishu_asset_mode": "degraded-with-backfill",
                    "version_anchor": {"git_commit_before": "abc123"},
                    "rollback_strategy": {"default_level": "unit"},
                }
            }
        )
        self.assertEqual(payload["unit_id"], "unit-001")
        self.assertEqual(payload["track"], "strategy-mainline")
        self.assertEqual(payload["feishu_asset_mode"], "degraded-with-backfill")
        self.assertEqual(payload["rollback_level"], "unit")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_hybrid_unit_dispatch_payload.py -v
```

Expected:

- FAIL because `build_hybrid_unit_dispatch_payload.py` does not exist

- [ ] **Step 3: 实现 payload builder**

Create `github-actions/build_hybrid_unit_dispatch_payload.py`:

```python
import json
import sys


def build_payload(raw):
    unit = raw.get("unit", {})
    rollback = unit.get("rollback_strategy") or {}
    version_anchor = unit.get("version_anchor") or {}
    return {
        "unit_id": unit.get("unit_id", ""),
        "unit_name": unit.get("unit_name", ""),
        "track": unit.get("track", ""),
        "feishu_asset_mode": unit.get("feishu_asset_mode", "full-sync"),
        "suggested_agents": list(unit.get("suggested_agents", [])),
        "acceptance_mode": (unit.get("acceptance_target") or {}).get("mode", ""),
        "rollback_level": rollback.get("default_level", ""),
        "rollback_owner": rollback.get("owner", ""),
        "git_commit_before": version_anchor.get("git_commit_before", ""),
        "workflow_run_id": version_anchor.get("workflow_run_id", ""),
    }


if __name__ == "__main__":
    json.dump(build_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 再写 checker 测试**

Create `github-actions/tests/test_check_hybrid_unit_dispatch.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "check_hybrid_unit_dispatch.py"
SPEC = importlib.util.spec_from_file_location("check_hybrid_unit_dispatch", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CheckHybridUnitDispatchTests(unittest.TestCase):
    def test_blocks_missing_rollback_level(self):
        result = MODULE.evaluate_payload(
            {
                "unit_id": "unit-001",
                "track": "strategy-mainline",
                "feishu_asset_mode": "degraded-with-backfill",
                "acceptance_mode": "chain-runnable",
                "rollback_level": "",
            }
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_ROLLBACK_STRATEGY_REQUIRED", result["reason_codes"])

    def test_passes_minimal_runnable_payload(self):
        result = MODULE.evaluate_payload(
            {
                "unit_id": "unit-001",
                "track": "strategy-mainline",
                "feishu_asset_mode": "degraded-with-backfill",
                "acceptance_mode": "chain-runnable",
                "rollback_level": "unit",
            }
        )
        self.assertEqual(result["decision"], "PASS")
```

- [ ] **Step 5: 实现 checker**

Create `github-actions/check_hybrid_unit_dispatch.py`:

```python
import json
import sys


def evaluate_payload(payload):
    reason_codes = []
    recommended_next_action = ""

    if not payload.get("unit_id"):
        reason_codes.append("RULE_UNIT_ID_REQUIRED")
    if not payload.get("track"):
        reason_codes.append("RULE_TRACK_REQUIRED")
    if not payload.get("acceptance_mode"):
        reason_codes.append("RULE_ACCEPTANCE_MODE_REQUIRED")
    if not payload.get("rollback_level"):
        reason_codes.append("RULE_ROLLBACK_STRATEGY_REQUIRED")
    if payload.get("feishu_asset_mode") not in {
        "full-sync",
        "degraded-with-backfill",
        "blocked-by-feishu-asset",
    }:
        reason_codes.append("RULE_INVALID_FEISHU_ASSET_MODE")

    if reason_codes:
        recommended_next_action = "governance: complete hybrid unit dispatch fields"

    return {
        "decision": "PASS" if not reason_codes else "BLOCK",
        "reason_codes": reason_codes,
        "recommended_next_action": recommended_next_action,
    }


if __name__ == "__main__":
    json.dump(evaluate_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_hybrid_unit_dispatch_payload.py github-actions/tests/test_check_hybrid_unit_dispatch.py -v
```

Expected:

- PASS for both builder and checker suites

- [ ] **Step 7: Commit**

```bash
git add github-actions/build_hybrid_unit_dispatch_payload.py github-actions/check_hybrid_unit_dispatch.py github-actions/tests/test_build_hybrid_unit_dispatch_payload.py github-actions/tests/test_check_hybrid_unit_dispatch.py
git commit -m "feat: add hybrid unit dispatch validator"
```

---

### Task 3: 新增 dispatch runner 与 workflow 入口

**Files:**
- Create: `github-actions/run_hybrid_unit_dispatch.py`
- Create: `github-actions/tests/test_run_hybrid_unit_dispatch.py`
- Create: `.github/workflows/collab-hybrid-unit-dispatch.yml`

- [ ] **Step 1: 为 runner 先写失败测试**

Create `github-actions/tests/test_run_hybrid_unit_dispatch.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_hybrid_unit_dispatch.py"
SPEC = importlib.util.spec_from_file_location("run_hybrid_unit_dispatch", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RunHybridUnitDispatchTests(unittest.TestCase):
    def test_build_dispatch_plan_defaults_to_existing_agents(self):
        plan = MODULE.build_dispatch_plan(
            {
                "unit_id": "unit-001",
                "suggested_agents": [],
                "feishu_asset_mode": "degraded-with-backfill",
                "rollback_level": "unit",
            }
        )
        self.assertEqual(
            plan["assigned_agents"],
            [
                "collab-developer-agent",
                "collab-validator-agent",
                "collab-governance-agent",
            ],
        )
        self.assertEqual(plan["feishu_asset_mode"], "degraded-with-backfill")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_hybrid_unit_dispatch.py -v
```

Expected:

- FAIL because `run_hybrid_unit_dispatch.py` does not exist

- [ ] **Step 3: 实现 runner**

Create `github-actions/run_hybrid_unit_dispatch.py`:

```python
import json
import sys


DEFAULT_AGENTS = [
    "collab-developer-agent",
    "collab-validator-agent",
    "collab-governance-agent",
]


def build_dispatch_plan(payload):
    assigned_agents = payload.get("suggested_agents") or DEFAULT_AGENTS
    return {
        "unit_id": payload.get("unit_id", ""),
        "assigned_agents": assigned_agents,
        "execution_order": [
            "dispatch",
            "developer",
            "validator",
            "governance",
        ],
        "acceptance_mode": payload.get("acceptance_mode", "chain-runnable"),
        "feishu_asset_mode": payload.get("feishu_asset_mode", "full-sync"),
        "rollback_level": payload.get("rollback_level", "unit"),
        "required_comments": [
            "STARTED",
            "TEST_REPORT",
            "VALIDATION_RESULT",
            "UPDATED",
        ],
    }


if __name__ == "__main__":
    json.dump(build_dispatch_plan(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 新增 workflow 入口**

Create `.github/workflows/collab-hybrid-unit-dispatch.yml`:

```yaml
name: collab-hybrid-unit-dispatch

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: "Target PR number"
        required: true
        type: string
      task_id:
        description: "Ledger task id"
        required: true
        type: string
      unit_id:
        description: "Hybrid unit id"
        required: true
        type: string

jobs:
  dispatch:
    runs-on: [self-hosted, macOS, workbuddy]
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main
          fetch-depth: 0

      - name: Build dispatch payload
        run: |
          python3 github-actions/build_hybrid_unit_dispatch_payload.py < ledger/templates/hybrid-unit-record.json > hybrid_dispatch_payload.json

      - name: Check dispatch payload
        run: |
          python3 github-actions/check_hybrid_unit_dispatch.py < hybrid_dispatch_payload.json > hybrid_dispatch_check.json
          python3 - <<'PY'
          import json
          data = json.load(open("hybrid_dispatch_check.json", encoding="utf-8"))
          if data["decision"] != "PASS":
              raise SystemExit(1)
          PY

      - name: Build dispatch plan
        run: |
          python3 github-actions/run_hybrid_unit_dispatch.py < hybrid_dispatch_payload.json > hybrid_dispatch_plan.json
```

- [ ] **Step 5: 运行测试并校验 workflow 结构**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_hybrid_unit_dispatch.py -v
python3 -m unittest github-actions/tests/test_collab_workflows_present.py -v
```

Expected:

- PASS for the new runner test
- Existing workflow presence tests still pass

- [ ] **Step 6: Commit**

```bash
git add github-actions/run_hybrid_unit_dispatch.py github-actions/tests/test_run_hybrid_unit_dispatch.py .github/workflows/collab-hybrid-unit-dispatch.yml
git commit -m "feat: add hybrid unit dispatch workflow"
```

---

### Task 4: 把回滚与飞书资产模式接入 ledger 与评论模板

**Files:**
- Create: `templates/pr-comment-hybrid-unit-dispatch.md`
- Create: `templates/pr-comment-rollback-decision.md`
- Modify: `github-actions/update_agent_ledger.py`
- Modify: `docs/superpowers/templates/agent-task-card.md`
- Modify: `github-actions/tests/test_update_agent_ledger.py`

- [ ] **Step 1: 为 ledger updater 先写失败测试**

Append to `github-actions/tests/test_update_agent_ledger.py`:

```python
class HybridRollbackRecordTests(unittest.TestCase):
    def test_task_template_exposes_rollback_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "task-record.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("rollback_strategy", data)
        self.assertIn("version_anchor", data)

    def test_noop_transition_keeps_state_change_false(self):
        task = {
            "status": "ledgered",
            "governance_closure": {
                "archive_summary": "x",
                "index_updates": ["docs/README.md"],
                "faq_decision": "x",
                "faq_entries": ["y"],
                "closure_agent": "SOLO",
                "closure_completed_at": "2026-06-07T00:00:00Z",
            },
        }
        _, result = MODULE.apply_status_transition(task, "ledgered")
        self.assertFalse(result["state_changed"])
```

- [ ] **Step 2: 新增 dispatch / rollback 评论模板**

Create `templates/pr-comment-hybrid-unit-dispatch.md`:

```md
[混合单元调度 / HYBRID_UNIT_DISPATCH]

Unit ID: <unit-id>
Track: <strategy-mainline>
Task ID: <task-id>
Feishu Asset Mode: <full-sync | degraded-with-backfill | blocked-by-feishu-asset>
Rollback Level: <unit | chain | asset>
Assigned Agents:
- collab-developer-agent
- collab-validator-agent
- collab-governance-agent
```

Create `templates/pr-comment-rollback-decision.md`:

```md
[回滚决策 / ROLLBACK_DECISION]

Unit ID: <unit-id>
Task ID: <task-id>
Rollback Level: <unit | chain | asset>
Reason Codes:
- <reason-code>
Next Required Action: <governance or developer follow-up>
```

- [ ] **Step 3: 扩展任务卡模板**

Modify `docs/superpowers/templates/agent-task-card.md` by adding:

```md
## Hybrid Unit
- Unit ID:
- Track:
- Feishu Asset Mode:
- Acceptance Mode:

## Version And Rollback
- Git Commit Before:
- PR Ref:
- Workflow Run ID:
- Feishu Asset Before Snapshot:
- Default Rollback Level:
- Rollback Owner:
```

- [ ] **Step 4: 扩展 ledger updater 以保留版本与回滚信息**

Modify `github-actions/update_agent_ledger.py` by adding this helper below `build_governance_closure()`:

```python
def normalize_version_anchor(anchor):
    anchor = anchor or {}
    return {
        "git_commit_before": anchor.get("git_commit_before", ""),
        "git_branch_or_pr_ref": anchor.get("git_branch_or_pr_ref", ""),
        "workflow_run_id": anchor.get("workflow_run_id", ""),
        "acceptance_request_id": anchor.get("acceptance_request_id", ""),
        "feishu_asset_before_snapshot": anchor.get("feishu_asset_before_snapshot", ""),
    }
```

Use it when preparing any ledger task write:

```python
task["version_anchor"] = normalize_version_anchor(task.get("version_anchor"))
```

- [ ] **Step 5: 运行回归测试**

Run:

```bash
python3 -m unittest github-actions/tests/test_update_agent_ledger.py -v
```

Expected:

- PASS for existing governance tests
- PASS for the new rollback-related assertions

- [ ] **Step 6: Commit**

```bash
git add templates/pr-comment-hybrid-unit-dispatch.md templates/pr-comment-rollback-decision.md docs/superpowers/templates/agent-task-card.md github-actions/update_agent_ledger.py github-actions/tests/test_update_agent_ledger.py
git commit -m "feat: add rollback-aware hybrid task surfaces"
```

---

### Task 5: 加入策略主线样板单元并更新入口文档

**Files:**
- Modify: `ledger/tasks/index.json`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/04-ENGINEERING-INDEX.md`

- [ ] **Step 1: 添加样板单元记录**

Append this task object to `ledger/tasks/index.json` and add its `task_id` to `open_tasks`:

```json
{
  "goal_id": "goal-strategy-mainline-dispatch-20260607",
  "task_id": "task-strategy-mainline-ticket-001",
  "parent_task_id": "",
  "title": "策略设置成功 -> 生成策略任务单（混合单元样板）",
  "source_type": "assigned",
  "task_type": "serial",
  "mode": "STANDARD",
  "status": "open",
  "depends_on": [],
  "dependency_gate": "planned",
  "shared_boundary": [
    "ledger/tasks/index.json",
    "templates/pr-comment-hybrid-unit-dispatch.md"
  ],
  "sync_checkpoint": [
    "docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md"
  ],
  "current_sync_state": "none",
  "owner_agent": "",
  "validator_agent": "Validator AGENT",
  "governance_agent": "Governance AGENT",
  "workspace_path": "DREAM-AGENT",
  "unit_id": "unit-strategy-task-ticket-001",
  "feishu_asset_mode": "degraded-with-backfill",
  "version_anchor": {
    "git_commit_before": "",
    "git_branch_or_pr_ref": "",
    "workflow_run_id": "",
    "acceptance_request_id": "",
    "feishu_asset_before_snapshot": ""
  },
  "rollback_strategy": {
    "default_level": "unit",
    "trigger": [
      "validator_direction_error",
      "acceptance_chain_failed"
    ],
    "owner": "Governance AGENT"
  },
  "next_required_action": "governance: dispatch hybrid unit and post STARTED"
}
```

- [ ] **Step 2: 更新 README 入口**

Add this bullet to `README.md` under the collaboration/docs section:

```md
- `docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md` — 混合单元编排、飞书一级正式能力、回滚模型
- `docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md` — 对应实施计划
```

Add this bullet to `docs/README.md`:

```md
- `docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md`
- `docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md`
```

Add this section to `docs/04-ENGINEERING-INDEX.md`:

```md
### 2.x Dream-Agent Hybrid Dispatch

- 设计：`docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md`
- 计划：`docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md`
- 样板单元：`task-strategy-mainline-ticket-001`
```

- [ ] **Step 3: 运行最小仓库回归**

Run:

```bash
python3 -m unittest github-actions/tests/test_update_agent_ledger.py github-actions/tests/test_build_hybrid_unit_dispatch_payload.py github-actions/tests/test_check_hybrid_unit_dispatch.py github-actions/tests/test_run_hybrid_unit_dispatch.py -v
git diff --check
```

Expected:

- All selected unittest suites pass
- `git diff --check` prints no whitespace errors

- [ ] **Step 4: Commit**

```bash
git add ledger/tasks/index.json README.md docs/README.md docs/04-ENGINEERING-INDEX.md docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md
git commit -m "docs: register hybrid dispatch sample unit"
```

---

## Self-Review

### Spec coverage

- `混合单元` 数据模型：Task 1
- `Hybrid Unit Dispatch` 统一入口：Task 2 + Task 3
- `飞书 CLI 一级正式能力`：Task 1 字段、Task 3 workflow、Task 4 模板
- `降级与回填机制`：Task 2 checker + Task 4 comments
- `版本管理与回滚机制`：Task 1 schema + Task 4 updater
- `策略主线首个样板单元`：Task 5

### Placeholder scan

- 未使用 `TODO` / `TBD`
- 每个任务都包含精确文件路径、代码片段、命令和预期结果

### Type consistency

- 统一使用 `unit_id`, `feishu_asset_mode`, `version_anchor`, `rollback_strategy`
- 调度输出统一使用 `acceptance_mode`, `rollback_level`
- 飞书模式只允许：`full-sync`, `degraded-with-backfill`, `blocked-by-feishu-asset`

---

Plan complete and saved to `docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

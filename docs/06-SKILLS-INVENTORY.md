---
id: 06-SKILLS-INVENTORY
type: reference
owner: ledger-protocol-agent
depends:
  - 01-COLLABORATION-PROTOCOL
version: 3
last_verified: 2026-06-08
---

# SKILLS Inventory

> Source of truth: `SKILLS/*/SKILL.md`

## 0. Rule of Thumb

- Before any code edits: run `dual-agent-conflict-gate`.
- If a rule/gate/protocol is unclear: stop and consult `docs/`.

## 1. Skills List

### 1.1 dual-agent-conflict-gate

- Spec: `SKILLS/dual-agent-conflict-gate/SKILL.md`
- Purpose: pre-flight conflict detection (branch policy, ownership boundaries, shared boundaries, contract freeze level).
- When to use: before every task; before scope expansion.

### 1.2 agent-standard-dev-lifecycle

- Spec: `SKILLS/agent-standard-dev-lifecycle/SKILL.md`
- Purpose: lifecycle phase orchestration (Phase 0-8).
- When to use: when you need to drive a task end-to-end with evidence checkpoints.

### 1.3 agent-design-review

- Spec: `SKILLS/agent-design-review/SKILL.md`
- Purpose: design review checklist and decisions (APPROVED/CHANGES_REQUESTED/REJECTED).
- When to use: before STARTED for non-trivial scope; always when gate requires DESIGN_REVIEW.

### 1.4 agent-dev-execution

- Spec: `SKILLS/agent-dev-execution/SKILL.md`
- Purpose: enforce dev execution order (plan → gate → STARTED → implement → evidence → DONE).
- When to use: when you are the active implementer of a scoped change.

### 1.5 agent-quality-test

- Spec: `SKILLS/agent-quality-test/SKILL.md`
- Purpose: generate `TEST_REPORT` with unit/integration/scenario evidence.
- When to use: before asking for validation or merge.

### 1.6 agent-collab-supervisor

- Spec: `SKILLS/agent-collab-supervisor/SKILL.md`
- Purpose: supervision of protocol evidence and branch compliance; used by lifecycle guard.
- When to use: when PR is blocked by lifecycle guard, to understand missing evidence.

### 1.7 task-decompose-blocks ⭐ (Phase D.5)

- Spec: `SKILLS/task-decompose-blocks/SKILL.md`
- Purpose: 将模块契约（Phase D）+ 前端页面定义（Phase C）拆解为具象的模块文件夹 + 任务区块结构。
- When to use: Phase D 完成后、Phase E 之前；将抽象契约转为物理区块文件。
- Trigger words: 任务拆解、区块生成、模块文件夹、生成区块、decompose blocks
- Output (五件套):
  1. 模块文件夹：`{workspace}/modules/{module-name}/`
  2. 任务区块：`{workspace}/modules/{module-name}/tasks/{N}-slug/BLOCK.md`
  3. 子工程索引：`{workspace}/modules/{module-name}/INDEX.md`
  4. 契约引用：`{workspace}/modules/{module-name}/contracts/phase-d.md`
  5. 总索引更新：`docs/file-registry.json` → `modules` 字段
- One-command usage:
  ```bash
  python3 SKILLS/task-decompose-blocks/decompose.py \
    --module market-quote \
    --pages docs/frontend-pages/market-quote.md \
    --contract docs/module-contracts/market-quote.md \
    --workspace 7-ARTIFACT-HUB-V2
  ```
- 批量模式：`--batch modules-list.json`

### 1.8 collab-ledger-planner ⭐

- Spec: `SKILLS/collab-ledger-planner/SKILL.md`
- Purpose: parse a technical plan/design Markdown into structured ledger tasks + sync workspace.
- When to use: when receiving a technical document to decompose into a `tasks/index.json` task list; when setting up a new workspace plan.
- Trigger words: 任务拆解、规划拆解、plan to tasks、生成任务清单、生成账本清单协议
- Output (three artifacts):
  1. `ledger/tasks/index.json` — new tasks written
  2. `ledger/protocols/{WORKSPACE}-LEDGER-{YYYYMMDD}.md` — protocol Markdown
  3. `{workspace}/PLAN.md` — task progress snapshot
- One-command usage:
  ```bash
  python3 SKILLS/collab-ledger-planner/ledger_sync.py sync \
    --plan <tech-doc.md> --goal-id <goal-x> --workspace 7-ARTIFACT-HUB-V2
  ```
- Post-task sync: `ledger_sync.py push-status --workspace 7-ARTIFACT-HUB-V2 --print-comment`
- Auto-sync: `.github/workflows/collab-ledger-sync.yml` fires on `index.json` changes to main

### 1.9 github-feishu-bot-bootstrap ⭐

- Spec: `SKILLS/github-feishu-bot-bootstrap/SKILL.md`
- Purpose: 作为 GitHub x 飞书长期入口技能，统一处理 Base / OKR / Wiki 接入、bot 权限、workflow 接线、E2E 联调与故障回补。
- When to use: 当需要把 GitHub workflow 接入飞书 Base / OKR / Wiki，或需要新建、复用、扩展、排障 GitHub x 飞书协作链路时。
- Trigger words: 飞书 bot、Feishu bot、GitHub 飞书集成、Base 联调、Lark bot、tenant_access_token
- Current live bootstrap notes: 已沉淀真实审批 smoke 经验，包含 `approval:approval` / `approval:instance` scope 验证、`form` 需序列化为 JSON 字符串、`ou_...` 申请人必须放在 `open_id`、以及 collab workflows 的 `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` 兼容设置。

## 2. Operational Scripts (Non-SKILL but Critical)

- Lifecycle payload builder: `github-actions/build_agent_lifecycle_payload.py`
- Lifecycle checker: `github-actions/check_agent_lifecycle.py`
- Collaboration payload builder/checker: `github-actions/build_agent_collaboration_payload.py`, `check_agent_collaboration.py`
- Ledger cycle runner: `github-actions/run_governance_ledger_cycle.py`
- Ledger updater: `github-actions/update_agent_ledger.py`
- **Ledger sync CLI**: `SKILLS/collab-ledger-planner/ledger_sync.py` (sync/push-status/status)
- **Plan parser**: `SKILLS/collab-ledger-planner/plan_to_tasks.py`

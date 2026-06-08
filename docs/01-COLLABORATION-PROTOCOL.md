---
id: 01-COLLABORATION-PROTOCOL
type: protocol
owner: ledger-protocol-agent
depends:
  - 00-AGENT-CONSTITUTION
version: 4
last_verified: 2026-05-20
---

# Collaboration Protocol (PR Comments + Gates)

> Status: active
> Scope: collaboration protocol for PR-based work in `dreambuddy-v1`

## 1. Canonical Anchors

Structured PR comments are the canonical collaboration interface.

### 1.1 分解线锚点（六步协作流）

六步协作流（技术文档 → 架构图 → 前端页面 → 模块契约 → 协作清单 → 验收标准）的前置产出锚点：

- `[技术文档 / TECHNICAL_SPEC]` — 业务目标、用户需求、非功能约束
- `[架构评审 / ARCHITECTURE_REVIEW]` — 工程架构图的目的性与数据流向评审
- `[前端页面定义 / FRONTEND_PAGES]` — 页面结构、组件层级、交互流程定义
- `[模块契约 / MODULE_CONTRACT]` — 模块间数据流、状态同步、异常处理契约
- `[协作清单 / COLLAB_CHECKLIST]` — 按模块拆分的任务清单与验收标准
- `[验收标准 / ACCEPTANCE_CRITERIA]` — 每个清单条目的可验证完成标准确认

### 1.2 执行线锚点（Phase 0-8）

任务进入执行线后的标准锚点：

- `[协作开工声明 / STARTED]`
- `[协作状态更新 / UPDATED]`
- `[协作阻塞通知 / BLOCKED]`
- `[方案评审记录 / DESIGN_REVIEW]`
- `[测试报告 / TEST_REPORT]`
- `[验收委托 / ACCEPTANCE_REQUEST]`
- `[验证结论 / VALIDATION_RESULT]`
- `[协作完成回报 / DONE]`
- `[账本同步 / LEDGER_SYNC]` ⭐ new — posted by CLI or GitHub Action when ledger/workspace state changes

Templates live in `templates/`.

## 2. Minimal Required Fields

### 2.0 分解线锚点（UI-Driven Flow）

以下锚点属于分解线（六步协作流），在执行线 Phase 0-1 之前完成：

#### 2.0.0 TECHNICAL_SPEC

- `Agent: <agent_id>`
- `Document:` 技术文档路径
- `Business Goal:` 一句话描述解决的用户问题
- `User Scenarios:` 列表
- `Non-Functional Constraints:` 性能/安全/合规
- `Scope Boundaries:` 包含/不包含

#### 2.0.1 ARCHITECTURE_REVIEW

- `Agent: <agent_id>`
- `Reviewer: <agent_id>`
- `Decision: APPROVED | CHANGES_REQUESTED`
- `Purpose:` 架构图如何服务于前端目的（而非纯技术分层）
- `Data Flow:` 数据源 → 服务层 → 前端模块（垂直切片）
- `Scope:` 覆盖的前端模块列表

#### 2.0.2 FRONTEND_PAGES

- `Agent: <agent_id>`
- `Pages:` 页面列表及对应组件
- `Components:` 每个组件的数据来源、触发条件、状态变化
- `Interactions:` 关键交互流程描述

#### 2.0.3 MODULE_CONTRACT

- `Agent: <agent_id>`
- `Module: <module_name>`
- `Upstream Output:` 上游模块输出格式与触发条件
- `Downstream Input:` 下游模块输入依赖与响应行为
- `Exception Path:` 异常/降级路径
- `State Sync:` 状态同步机制

#### 2.0.4 COLLAB_CHECKLIST

- `Agent: <agent_id>`
- `Tasks:` 按前端模块拆分的任务列表
- `Execution Type:` `parallel | serial | shared-sync`（每个任务）
- `Dependencies:` 任务间依赖关系
- `Acceptance Criteria:` 每个任务的可验证完成标准

#### 2.0.5 ACCEPTANCE_CRITERIA

- `Agent: <agent_id>`
- `Validator: <agent_id>`
- `Decision: CONFIRMED | NEEDS_REVISION`
- `Tasks Covered:` 清单条目列表
- `Criteria:` 每个条目的可验证完成标准（必须：可执行/可量化/独立于实现路径）

### 2.1 STARTED

- `Agent: <agent_id>`
- `任务: <task_name>`
- `Task ID: <task_id>`
- `分支: <agent/*>`
- `Workspace Path: <path>` (default `7-ARTIFACT-HUB-V2`; must be explicit if different)
- `计划修改:` list
- `占用范围:` list (strong-sync boundaries)
- `冲突门禁结果:` decision + reason_codes

### 2.2 DESIGN_REVIEW

- `Agent: <agent_id>`
- `Reviewer: <agent_id>` (must be present; reviewer must be non-owner for lifecycle gate)
- `Decision: APPROVED | CHANGES_REQUESTED | REJECTED`
- `Scope:` list

### 2.3 TEST_REPORT

- `Tester: <agent_id>`
- `Decision: TEST_PASS | TEST_FAIL | RISK_ACCEPTED`
- Evidence (commands, artifacts, paths)

### 2.4 VALIDATION_RESULT

- `Validator: <agent_id>`
- `Decision: ACCEPTED | REWORK | BLOCK`
- `Score: <0-100>`
- `Governance Handoff: ledgered | archived | pending`

### 2.5 ACCEPTANCE_REQUEST

- `Acceptance Request ID`
- `Acceptance Cycle ID`
- `Work Item ID`
- `Request Type`
- `Request Mode`
- `Source of Truth`
- `Target PR`
- `Lark Base URL`
- `Lark Table ID`
- `Lark Record ID`
- `验收对象`
- `验收范围`
- `业务上下文映射`
- `重点验收项`
- `本轮不要求`
- `期望回写格式`

Notes:

- `DONE != ACCEPTED`
- `DONE` means delivery is complete; `VALIDATION_RESULT` is the acceptance conclusion.

### 2.6 acceptance_cycle

- `acceptance_cycle` 是 `Acceptance Orchestration V2` 的编排中心对象
- 真源载体位于 `ledger/acceptance_cycles/*.json`
- 正式验收结论仍只允许落在 GitHub `VALIDATION_RESULT`
- 飞书只提供上下文与摘要回写，不写入第二份正式主结论

### 2.7 DONE

- `Agent: <agent_id>`
- `提交: <commit sha>`
- Delivery summary

### 2.8 LEDGER_SYNC (new)

- `Sync Agent: CLI | GitHub Action`
- `Protocol File: <path to LEDGER-YYYYMMDD.md>`
- `Changed Tasks:` list of `<task_id>: <old> → <new>` (CLI may print `old -> new`)
- `Workspace Updated: <workspace>/PLAN.md`
- `Ledger SHA: <before> → <after>`
- `Sync Time: <ISO8601>`

This anchor is posted automatically by `ledger_sync.py push-status --print-comment` or by the `collab-ledger-sync.yml` GitHub Action. It is informational and does not trigger lifecycle gate checks.

Notes:

- `Changed Tasks` is a sync-facing snapshot message, not a strict diff audit. If the old status cannot be derived, `old_status` may be `?`, but `Ledger SHA` MUST be present.
- Optional fields (backward compatible):
  - `Workspace: <workspace_path>`
  - `Sync State File: <workspace>/.ledger-sync.json`
  - `Protocol Version: v1`
  - `Generator: collab-ledger-planner@2.0`

## 3. Scope Change Rule (Fail-Closed)

- Any change that expands scope MUST post `[UPDATED]` first.
- If scope touches outside default workspace, it MUST be explicitly declared.

## 4. Block Rule (Fail-Closed)

- If execution cannot continue, post `[BLOCKED]` and stop.
- A blocked PR must not be force-pushed with unrelated changes to "unstick" gates.

## 5. Gates

### 5.1 分解线门禁（Phase A-F + D.5）

分解线各步骤按顺序推进，不可跳步：

- 技术文档 → 架构图 → 前端页面 → 模块契约 → **任务拆解区块（D.5）** → 协作清单 → 验收标准
- 每个步骤必须在 PR 中留下对应的结构化评论锚点（见 Section 1.1）
- Phase D.5 生成模块文件夹 + BLOCK.md 区块结构，Agent 开工前读区块头即可
- 七步完成后，协作清单条目才可进入执行线

### 5.2 执行线门禁（Phase 0-8）

- Lifecycle guard is enforced by repo workflows and validates:
  - architecture review present (分解线已走完)
  - frontend pages defined (前端页面定义完成)
  - module contracts defined (模块契约完成)
  - collab checklist posted (协作清单已发布)
  - task card present
  - design review present
  - started present
  - test report present
  - done present
  - non-owner review present
  - branch policy valid
  - shared files declared

If a gate fails, treat it as an instruction to produce missing protocol evidence, not as something to bypass.

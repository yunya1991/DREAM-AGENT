---
id: 04-ENGINEERING-INDEX
type: index
owner: ledger-protocol-agent
depends:
  - 00-AGENT-CONSTITUTION
  - 01-COLLABORATION-PROTOCOL
  - 02-ARCHITECTURE
version: 4
last_verified: 2026-06-07
---

# Engineering Index

> Status: active  
> Purpose: quickly locate the correct file to change  
> Last updated: 2026-06-07

## 1. Directories

- `docs/`: protocol source-of-truth docs
- `templates/`: PR comment templates
- `SKILLS/`: SKILL specs and guard configurations
- `github-actions/`: gate checkers, payload builders, ledger cycle runner
- `ledger/`: tasks and rewards ledgers
- `docs/superpowers/contracts/`: frozen contracts registry and schemas

## 2. What to Edit (Common Tasks)

### 2.1 Protocol Wording / Constitution / FAQs

- edit `docs/00-AGENT-CONSTITUTION.md`
- edit `docs/01-COLLABORATION-PROTOCOL.md`
- edit `docs/05-FAQ.md`

### 2.2 Add/Change PR Comment Templates

- edit `templates/*.md`
- lifecycle parsing logic: `github-actions/build_agent_lifecycle_payload.py`

### 2.3 Change Lifecycle Gate Rules

- rules: `SKILLS/agent-collab-supervisor/rules.json`
- checkers: `github-actions/check_agent_lifecycle.py`

### 2.4 Change Ledger or Reward Logic

- runner/controller: `github-actions/run_governance_ledger_cycle.py`
- ledger updater: `github-actions/update_agent_ledger.py`
- ledgers:
  - `ledger/tasks/index.json`
  - `ledger/rewards/index.json`

### 2.5 Conflict Gate Behavior / Boundaries

- behavior: `SKILLS/dual-agent-conflict-gate/conflict_gate.py`
- boundaries & contracts: `SKILLS/dual-agent-conflict-gate/gatekeeper_config.json`

### 2.6 GitHub x 飞书接入 / 排障 / 案例

- 接入规范：`docs/github-feishu-integration-handbook.md`
- 故障手册：`docs/github-feishu-troubleshooting.md`
- E2E 案例索引：`docs/github-feishu-e2e-case-index.md`
- 设计总览：`docs/github-feishu-okr-knowledgebase-design.md`

## 3. Gate Evidence Checklist (Where to Look)

### 3.1 分解线（UI-Driven Flow）

- TECHNICAL_SPEC: PR comment (`templates/tech-spec.md`)
- ARCHITECTURE_REVIEW: PR comment (`templates/architecture-review-comment.md`)
- FRONTEND_PAGES: PR comment (`templates/frontend-pages-comment.md`)
- MODULE_CONTRACT: PR comment (`templates/module-contract-comment.md`)
- COLLAB_CHECKLIST: checklist template (`templates/collab-checklist.md`)
- ACCEPTANCE_CRITERIA: PR comment (`templates/acceptance-criteria-comment.md`)

### 3.2 执行线（Phase 0-8）

- Task Card: PR body (`.github/pull_request_template.md`)
- DESIGN_REVIEW: PR comment (`templates/design-review-comment.md`)
- STARTED: PR comment (`templates/pr-comment-started.md`)
- TEST_REPORT: PR comment (`templates/test-report-comment.md`)
- VALIDATION_RESULT: PR comment (`templates/pr-comment-validation-result.md`)
- DONE: PR comment (`templates/pr-comment-done.md`)

## 4. UI-Driven Flow Documents (Where to Write)

- 技术文档：`docs/tech-spec-*.md`
- 工程架构图：`docs/architecture-*.md`
- 前端页面定义：`docs/frontend-pages/*.md`
- 模块契约：`docs/module-contracts/*.md`

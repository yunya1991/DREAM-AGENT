# AGENT Collaboration File Cabinet

This folder is the source-of-truth for AGENT collaboration in this repository.

## 0. Active Canonical Docs (Read First)

- `00-AGENT-CONSTITUTION.md` (fail-closed rules, hard boundaries, escalation)
- `01-COLLABORATION-PROTOCOL.md` (PR comment anchors, required fields, gates)
- `02-ARCHITECTURE.md` (roles + system chain + source-of-truth files)
- `03-WORKFLOWS-AND-NORMS.md` (execution workflow + norms)
- `04-ENGINEERING-INDEX.md` (where to edit what)
- `05-FAQ.md` (common failures and fixes)
- `06-SKILLS-INVENTORY.md` (skills list and when to use them)

## 1. Current Default Collaboration Mode

- Default workspace: `7-ARTIFACT-HUB-V2/**`
- Each AGENT opens its own PR on `agent/*` branch
- Roles are split: Ledger/Protocol vs Governance

See `agent-efficient-collaboration-mode.md` and `agent-ledger-protocol-vs-governance-short-spec.md`.

## 2. Design & Implementation Documents (Reference)

- `agent-ledger-protocol-vs-governance-short-spec.md`
- `agent-efficient-collaboration-mode.md`
- `agent-standard-dev-lifecycle-design.md`
- `agent-standard-dev-lifecycle-implementation-plan.md`
- `agent-collaboration-system-v1-design.md`
- `agent-collaboration-system-v1-implementation-plan.md`
- `agent-collaboration-system-v1-governance-agent-implementation-plan.md`
- [agent-collaboration-system-v1-governance-cycle-implementation-plan.md](agent-collaboration-system-v1-governance-cycle-implementation-plan.md)
- `self-hosted-runner.md` (trialed on PR9)
- `dual-agent-collaboration-foundation-design.md` (legacy subset reference)
- `github-feishu-okr-knowledgebase-design.md`
- `docs/superpowers/specs/2026-06-07-dream-agent-hybrid-unit-dispatch-design.md`
- `docs/superpowers/plans/2026-06-07-dream-agent-hybrid-unit-dispatch-implementation.md`
- `docs/superpowers/specs/2026-06-07-github-feishu-collaboration-closure-repair-design.md`
- `docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md`
- `docs/superpowers/specs/2026-06-07-feishu-goal-driven-progress-and-risk-approval-design.md`
- `docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md`

## 3. GitHub x 飞书协作文档

- [feishu-collab/README.md](./feishu-collab/README.md) - 飞书协作体系总入口（治理、技能注册表、runbook、handoff、审计）
- `github-feishu-integration-handbook.md` (接入规范)
- `github-feishu-troubleshooting.md` (故障排查手册)
- `github-feishu-e2e-case-index.md` (真实 E2E 案例索引)
- `github-feishu-new-base-e2e-runbook.md` (新 Base 接入真实 E2E 执行清单)
- `github-feishu-okr-knowledgebase-design.md` (OKR 与知识库建设设计)

## 4. Migration Notes

- Historical sources may exist under `docs/superpowers/specs/` and `docs/superpowers/plans/`.
- Those original paths are kept as compatibility stubs（兼容壳）for old links and PR discussions.

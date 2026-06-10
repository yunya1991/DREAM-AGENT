# Runbook Index

## Categories

- Change runbooks
- Cross-system reconciliation runbooks
- Fault-isolation runbooks
- Recovery runbooks

## Default Rule

Every production-facing skill execution that changes online state must end with a runbook-valid verification path or a documented gap.

## Entries

| Runbook | Path | Purpose |
| --- | --- | --- |
| Approval task-feishu-approval-smoke-001 Runbook | `docs/feishu-collab/runbooks/approval-task-feishu-approval-smoke-001-runbook.md` | Track Approval task-feishu-approval-smoke-001 Runbook recovery and verification |
| Feishu Token Strategy | `docs/feishu-collab/runbooks/feishu-token-strategy.md` | Choose between application identity and user identity tokens, and store the related credentials safely for workflow use |
| Final Acceptance Checklist | `docs/feishu-collab/runbooks/final-acceptance-checklist.md` | Validate the merged mainline end to end and hand off operator evidence across approval, writeback, and knowledge materialization |
| Mainline Operations Table | `docs/feishu-collab/runbooks/mainline-operations-table.md` | Provide a one-page operator view of trigger conditions, required inputs, outputs, and dependencies for the current mainline chain |
| Knowledge Materialization | `docs/feishu-collab/runbooks/knowledge-materialization.md` | Materialize approval and polling artifacts into governed runbook and handoff documents |
| Five Skill Integration Rehearsal | `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` | Run the fixture-driven full-chain rehearsal and interpret the normalized result |
| Real Approval Trigger | `docs/feishu-collab/runbooks/real-approval-trigger.md` | Create a real approval instance and capture the first approval-status evidence |
| Approval Polling Writeback | `docs/feishu-collab/runbooks/approval-polling-writeback.md` | Query an existing approval instance and write the normalized task/goal state back to Base |
| Automation Recovery Policy | `docs/feishu-collab/runbooks/automation-recovery-policy.md` | Define which local schedules may resume as read-only or dispatch-only flows and which must remain paused after mainline protection |

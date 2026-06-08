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
| Five Skill Integration Rehearsal | `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` | Run the fixture-driven full-chain rehearsal and interpret the normalized result |
| Real Approval Trigger | `docs/feishu-collab/runbooks/real-approval-trigger.md` | Create a real approval instance and capture the first approval-status evidence |
| Approval Polling Writeback | `docs/feishu-collab/runbooks/approval-polling-writeback.md` | Query an existing approval instance and write the normalized task/goal state back to Base |

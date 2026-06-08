# Approval task-feishu-approval-smoke-001 Runbook

## Trigger

- Approval Instance Code: `7ED36C95-AACF-4921-84E1-3220557153E6`

## Scope

- Task ID: `task-feishu-approval-smoke-001`
- Goal ID: `goal-feishu-approval`

## Preconditions

- Approval Status: `approved`
- Automation Status: `proceed`

## Detection

- Decision Summary: `approved:task-feishu-approval-smoke-001`

## Investigation Steps

- Review approval artifact and writeback artifact.

## Recovery Steps

- Continue from the current approval and Base writeback state.

## Verification

- Task Writeback: `success`
- Goal Writeback: `success`

## Escalation

- Escalate if status and Base writeback drift again.

## Evidence To Capture

- Approval Instance Code: `7ED36C95-AACF-4921-84E1-3220557153E6`
- Task ID: `task-feishu-approval-smoke-001`
- Goal ID: `goal-feishu-approval`

## Follow-up Knowledge Update

- Sync handoff after state changes.

# Execution Checklist

## Gate Review

- Confirm the action is high risk
- Confirm the trigger reason is explicit
- Confirm the timeout policy is visible

## Approval Request Gate

- Confirm `approval_code` is present
- Confirm `applicant_open_id` is present
- Confirm `form` is serialized as JSON string before submit
- Confirm instance external ID maps to the target task

## Polling Gate

- Confirm existing instance is reused when available
- Confirm approval status is mapped to collaboration state
- Confirm automation status is updated consistently

## Verification Gate

- Confirm approval status projection exists
- Confirm evidence snapshot exists
- Confirm handoff and `KnowledgeUpdate` are emitted

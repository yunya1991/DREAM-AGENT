# Escalation Policy

## Hard Block

- Missing `approval_code`
- Missing `applicant_open_id`
- Missing target task or goal record

## Soft Block

- Approval instance lookup failed
- Status projection gap detected
- Timeout policy conflict detected

## Degraded Success

- Approval result written back but evidence snapshot missing
- Approval result written back but handoff evidence incomplete

## Fallback

- `pause` when unsafe to continue
- `conservative_continue` only when explicitly marked safe

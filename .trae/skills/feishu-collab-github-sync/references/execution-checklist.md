# Execution Checklist

## Intake Gate

- Confirm the event is issue, PR, or checks related
- Confirm repository and object number are visible
- Confirm Feishu task and goal context are available

## Preview Gate

- Confirm event summary is readable
- Confirm field updates are visible before writeback
- Confirm `event_coverage_hit` is recorded
- Confirm `risk_flags` are recorded

## Writeback Gate

- Event coverage checked first
- Collaboration state writeback recorded
- Automation result writeback recorded
- Comment anchor writeback recorded when present

## Verification Gate

- Task record lookup confirmed
- Coverage gap outcome recorded
- Automation summary recorded
- Handoff and `KnowledgeUpdate` emitted

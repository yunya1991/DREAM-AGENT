# Final Acceptance Checklist

## Purpose

Provide an operator-facing acceptance checklist for the full Feishu collaboration chain after the new workflows are available on `main`.

## Preconditions

- Confirm the target branch is merged into `main`
- Confirm GitHub Actions can dispatch `.github/workflows/real-approval-trigger.yml`
- Confirm GitHub Actions can dispatch `.github/workflows/approval-polling-writeback.yml`
- Confirm GitHub Actions can dispatch `.github/workflows/knowledge-materialization.yml`
- Confirm repository secrets `LARK_APP_ID` and `LARK_APP_SECRET` exist
- Confirm the operator reviewed `docs/feishu-collab/runbooks/feishu-token-strategy.md`
- Confirm the operator has valid `approval_code` and `applicant_open_id`
- Confirm the operator knows `base_token`, `task_table_id`, `task_record_id`, `goal_table_id`, and `goal_record_id`

## Stage 1: Real Approval Trigger

- Dispatch `.github/workflows/real-approval-trigger.yml`
- Provide `approval_code`, `applicant_open_id`, `task_payload_json`, and `goal_payload_json`
- Wait for a green run and save the workflow run URL
- Download `approval_dispatch_result.json` and confirm it exists
- Download `approval_status_result.json` and confirm it exists
- Record the emitted `approval_instance_code`
- In Feishu approval, verify the instance is visible by template name and instance code

## Stage 2: Real Polling And Writeback

- Dispatch `.github/workflows/approval-polling-writeback.yml`
- Provide `approval_instance_code`, `decision_id`, `task_payload_json`, `goal_payload_json`, and `base_sync_json`
- Wait for a green run and save the workflow run URL
- Download `approval_status_result.json` and confirm it exists
- Download `approval_writeback_result.json` and confirm it exists
- In Feishu Base task record, verify `审批状态`, `自动化状态`, and `决策摘要`
- In Feishu Base goal record, verify `当前状态`, `最近决策摘要`, and `workflow_signal`

## Stage 3: Knowledge Materialization

- Dispatch `.github/workflows/knowledge-materialization.yml`
- Provide `approval_status_result_json`, `approval_writeback_result_json`, and `materialization_context_json`
- Wait for a green run and save the workflow run URL
- Download `knowledge_materialization_result.json` and confirm it exists
- Verify `docs/feishu-collab/runbooks/approval-<task_id>-runbook.md` exists
- Verify `docs/feishu-collab/handoffs/approval-<task_id>-handoff.md` exists
- Verify `docs/feishu-collab/RUNBOOK_INDEX.md` contains exactly one matching runbook entry
- Verify `docs/feishu-collab/HANDOFF_INDEX.md` contains exactly one matching handoff entry

## Stage 4: Scope And Access Check

- If local approval instance re-query fails, confirm whether the operator account has `approval:instance:read`
- If `tenant_access_token` fails for a user-auth API, switch to `user_access_token` and verify with `lark-cli --as user`
- If `approval:instance:read` is missing, record the gap and continue validating from workflow artifacts and downstream Base updates
- If `approval:instance:read` is present, run the second query and capture the returned approval status as final evidence

## Acceptance Criteria

- A real approval instance is created successfully
- Task writeback is confirmed in the real Base record
- Goal writeback is confirmed in the real Base record
- A real runbook document is materialized
- A real handoff document is materialized
- `RUNBOOK_INDEX.md` is updated
- `HANDOFF_INDEX.md` is updated
- The operator can hand off all evidence without guessing any missing step

## Failure Handling

- If approval creation fails, inspect the workflow summary, inspect `approval_dispatch_result.json`, and re-check `approval_code` plus `applicant_open_id`
- If polling or writeback fails, inspect `approval_status_result.json`, inspect `approval_writeback_result.json`, and re-check Base routing values
- If knowledge materialization fails, inspect `knowledge_materialization_result.json`, verify whether files were partially written, and repair indexes if the failure is index-only

## Handoff Output

- Capture workflow run URLs for all three stages
- Capture the final `approval_instance_code`
- Capture the `task_record_id` and `goal_record_id`
- Capture the generated runbook path
- Capture the generated handoff path
- Capture any remaining access or scope gaps

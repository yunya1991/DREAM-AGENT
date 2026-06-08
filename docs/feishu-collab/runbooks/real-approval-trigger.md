# Real Approval Trigger

## Purpose

Run a real Feishu approval creation flow and immediately query the created instance once.

## Workflow Entry

- Workflow: `.github/workflows/real-approval-trigger.yml`
- Trigger: `workflow_dispatch`
- Required inputs:
  - `approval_code`
  - `applicant_open_id`
  - `task_payload_json`
  - `goal_payload_json`

## Secrets

- `LARK_APP_ID`
- `LARK_APP_SECRET`

## Artifacts

- `approval_dispatch_result.json`
- `approval_status_result.json`

## Success Rule

The workflow succeeds only when the approval instance is created and the follow-up query returns a valid approval status.

## Evidence First

Even on failure, keep the uploaded artifacts and the Job Summary. They are the primary debugging evidence for this stage.

## Next Step

After the approval instance exists, use `.github/workflows/approval-polling-writeback.yml` to continue from status evidence into task/goal writeback.

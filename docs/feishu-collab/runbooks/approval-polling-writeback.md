# Approval Polling Writeback

## Purpose

Query an existing Feishu approval instance, project the result into normalized approval fields, and write the latest task and goal state back to Feishu Base.

## Workflow Entry

- Workflow: `.github/workflows/approval-polling-writeback.yml`
- Trigger: `workflow_dispatch`
- Required inputs:
  - `approval_instance_code`
  - `decision_id`
  - `task_payload_json`
  - `goal_payload_json`
  - `base_sync_json`
- Optional inputs:
  - `sibling_tasks_json`

## Secrets

- `LARK_APP_ID`
- `LARK_APP_SECRET`

## Artifacts

- `approval_status_result.json`
- `approval_writeback_result.json`

## Success Rule

The workflow succeeds only when the approval query returns a valid status and both the task and goal writebacks succeed.

## Failure Guide

- If the query fails, inspect `approval_status_result.json` first.
- If task writeback fails, fix the task writeback route and rerun before touching goal writeback.
- If goal writeback fails, keep the task receipt, repair the goal route, and rerun.

# Mainline Operations Table

## Scope

This page is the operator-facing one-page table for the current mainline automation chain:

- GitHub remains the execution spine.
- Feishu remains the real side-effect system.
- Monitoring and rehearsal remain compensating controls.
- Local automation must stay dispatch-only and must not write code or online state directly.

## Execution Order

| Stage | Workflow | Trigger Condition | Required Inputs | Outputs | Upstream Dependencies | Downstream Dependencies |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `five-skill-rehearsal` | Run first when resuming the chain, changing contracts, rotating credentials, or before a first real run in a new session | `scenario_id` | `five-skill-rehearsal-report.json`, workflow summary | Registered rehearsal scenario, self-hosted runner, repository checkout | If `system_status=pass`, proceed to Stage 1. If not, stop and repair contracts first. |
| 1 | `real-approval-trigger` | Run when a real approval instance must be created in Feishu | `approval_code`, `applicant_open_id`, `task_payload_json`, `goal_payload_json` | `approval_dispatch_result.json`, `approval_status_result.json`, workflow summary | `LARK_APP_ID`, `LARK_APP_SECRET`, valid approval definition, valid applicant identity | Provides `approval_instance_code` and `decision_id` to Stage 2. |
| 2 | `approval-polling-writeback` | Run after Stage 1 succeeds and an existing approval instance must be polled and written back to Base | `approval_instance_code`, `decision_id`, `task_payload_json`, `goal_payload_json`, `base_sync_json`; optional `sibling_tasks_json` | `approval_status_result.json`, `approval_writeback_result.json`, workflow summary | Stage 1 outputs, Feishu token minting, Base routing payload, self-hosted runner | Provides normalized approval status and writeback result to Stage 3. |
| 3 | `knowledge-materialization` | Run after Stage 2 succeeds and governed knowledge outputs must be generated | `approval_status_result_json`, `approval_writeback_result_json`, `materialization_context_json` | `knowledge_materialization_result.json`, generated runbook/handoff/index updates inside the workflow workspace | Stage 2 artifacts, materialization context, repository write permission | Produces governed knowledge evidence for acceptance, handoff, and audit review. |
| 4 | `agent-protocol-monitor` | Run on schedule or manually after a real run when protocol drift, ledger drift, or memory drift must be checked | None | Updated protocol memory files, sync state, ledger changes when needed | Open task index, protocol docs, self-hosted runner | Feeds operator review and drift correction; does not replace Stages 1-3. |

## Optional Dispatch Layer

| Workflow | Trigger Condition | Required Inputs | Outputs | Upstream Dependencies | Downstream Dependencies |
| --- | --- | --- | --- | --- | --- |
| `collab-hybrid-unit-dispatch` | Use only when a PR-scoped hybrid unit needs GitHub-side dispatch planning and audit evidence | `pr_number`, `task_id`, `unit_id` | `hybrid_dispatch_payload.json`, `hybrid_dispatch_check.json`, `hybrid_dispatch_plan.json` | Ledger task context, hybrid unit template, target PR | Hands work to developer/validator/governance agents; not required for the Feishu approval mainline itself |

## Current Operator Rules

- Preferred real-run order is `five-skill-rehearsal` -> `real-approval-trigger` -> `approval-polling-writeback` -> `knowledge-materialization` -> `agent-protocol-monitor`.
- `controlled-dispatch` is the intended allowlist wrapper in recovery design, but it is not present in the current main repository state; do not treat it as the only available entrypoint until it is restored on `main`.
- A local scheduled task may prepare inputs or call GitHub dispatch, but it must not directly mutate repository code, PR state, or Feishu state without a corresponding GitHub Actions evidence trail.
- `knowledge-materialization` currently proves execution success through artifacts and workflow logs; it does not by itself prove changes were committed back to `main`.
- If any stage fails, stop the chain and keep the failure artifact as the audit anchor for the next repair step.

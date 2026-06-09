# Automation Recovery Policy

## Trigger

Use this policy when deciding whether a paused local schedule may be resumed after `main` is protected by PR checks and `.github/workflows/controlled-dispatch.yml` is available.

## Scope

This policy covers local scheduled sessions, cron-like desktop automation, and operator-owned launch agents that touch `DREAM-AGENT` or trigger Feishu collaboration workflows from a local machine.

## Preconditions

- `main` remains protected and changes land through PRs only
- `drift-guard` and `lifecycle-guard` are active on pull requests
- Operators can trigger `workflow_dispatch` runs through GitHub CLI or the GitHub UI
- Replacement workflows exist in GitHub Actions for write paths:
  - `.github/workflows/controlled-dispatch.yml`
  - `.github/workflows/real-approval-trigger.yml`
  - `.github/workflows/approval-polling-writeback.yml`
  - `.github/workflows/knowledge-materialization.yml`

## Detection

Treat a local automation as recoverable only when all of the following are true:

- It is read-only against the repo worktree, remote branches, and production data stores
- It does not commit, rebase, merge, push, or open/update PR branches on a timer
- Its write side effect, if any, is limited to dispatching an allowlisted GitHub workflow
- It can emit auditable evidence such as a run URL, artifact URL, job summary, or operator log

Treat a local automation as permanently disabled when any of the following are true:

- It writes repo files on a schedule
- It pushes directly to `main` or any integration branch
- It mutates the working tree and depends on a long-lived dirty workspace
- It bypasses PR review, `drift-guard`, `lifecycle-guard`, or GitHub artifact retention

## Investigation Steps

1. Classify the local schedule as one of:
   - Read-only inspection
   - Dispatch-only trigger
   - Repo-writing scheduled execution
2. Confirm whether the schedule can be rewritten to produce deterministic JSON inputs and call `gh workflow run`.
3. Confirm the target workflow is allowlisted by `.github/workflows/controlled-dispatch.yml`.
4. Confirm the operator can capture the resulting run URL, artifacts, and any Feishu writeback evidence.
5. If any step fails, keep the local schedule paused.

## Recovery Steps

### Allowed Local Automation

The following local automation categories may be resumed:

- Read-only inspection:
  - `git status`, `git log`, artifact directory diff, workflow status polling, health checks
  - output may be written to an operator-owned report location outside repo automation paths
- Dispatch-only execution:
  - generate deterministic `trigger_inputs_json`
  - call `gh workflow run controlled-dispatch.yml`
  - never modify tracked repo files as part of the scheduled session

### Permanently Disabled Local Automation

The following local automation categories must remain disabled:

- Any scheduled session that writes repo content and then commits or pushes
- Any timed job that attempts to advance `main` without a PR
- Legacy local chains that depend on PR9-only developer, validator, or governance automation
- Any flow that creates side effects in Feishu or GitHub without an auditable Actions run

### Current Paused Schedule Mapping

| Local schedule | Recommended state | Local permission | Replacement path |
| --- | --- | --- | --- |
| `Dream-Agent Hybrid Dispatch Executor` | Keep paused until converted | Dispatch-only plus read-only inspection | Trigger `.github/workflows/controlled-dispatch.yml`, then choose `real-approval-trigger`, `approval-polling-writeback`, or `knowledge-materialization` via `trigger_target` |
| `dream-acceptance-hourly` | May resume after target repo, URLs, and baseline are updated | Read-only inspection only; dispatch manually when a write path is needed | Use read-only checks locally, then route any write action through `.github/workflows/controlled-dispatch.yml` |
| `Protocol Ledger Agent (dreambuddy-v1)` | Long-term paused | None | No replacement in `DREAM-AGENT`; keep isolated from current mainline |
| `PR9 Developer/Validator/Governance` | Long-term paused | None | No replacement; deprecated for current mainline flow |

## Verification

### Return To Mainline Flow

Use this checklist whenever a local operator wants to resume an automation-adjacent delivery flow:

1. Open a PR from an allowed branch prefix such as `protocol/`, `design/`, or `milestone/`.
2. Fill the PR body with the minimum task card fields required by `lifecycle-guard`.
3. Wait for PR checks, including `drift-guard` and `lifecycle-guard`, to pass.
4. Trigger `.github/workflows/controlled-dispatch.yml` with:
   - `change_class`
   - `trigger_target`
   - `trigger_inputs_json`
5. Record the dispatched run URL and any produced artifact URLs.
6. Complete Feishu follow-up through the dispatched workflows:
   - `real-approval-trigger` for approval creation
   - `approval-polling-writeback` for Base writeback
   - `knowledge-materialization` for runbook and handoff artifacts
7. Confirm the chain leaves an auditable evidence trail:
   - PR link
   - green checks
   - Actions run URL
   - artifact names and download links
   - Feishu writeback or monitoring result

### Minimum Dispatch Example

```bash
gh workflow run controlled-dispatch.yml \
  --ref main \
  -f change_class=mainline \
  -f trigger_target=knowledge-materialization \
  -f trigger_inputs_json='{}'
```

## Escalation

- If a local schedule still needs repo write access, do not resume it; redesign the flow around GitHub Actions first.
- If the desired target is not in the `controlled-dispatch` allowlist, add governance review before any recovery work.
- If `drift-guard` or `lifecycle-guard` blocks the PR, fix the protocol gap instead of bypassing the guard.

## Evidence To Capture

- The local schedule name and its classification
- The approved replacement workflow or the reason it remains paused
- PR URL and final merge status
- `controlled-dispatch` run URL
- Artifact names such as `drift-guard-report-<run_id>` or workflow-specific evidence bundles
- Feishu approval, writeback, monitoring, or knowledge-materialization references

## Follow-up Knowledge Update

- Update this policy when a paused local schedule is converted into a read-only or dispatch-only flow.
- Add new allowlisted workflows here before operators are told to resume related local automation.
- If a schedule is retired permanently, keep its mapping entry and mark it deprecated so future operators do not attempt to revive it blindly.

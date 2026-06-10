# Drift Guard Cross-Repo Reuse + Automation Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Dreambuddy-V2 off the vendored drift-guard implementation and reuse DREAM-AGENT workflow+action via a pinned Git tag; publish an automation recovery policy and return to mainline automation flow.

**Architecture:** DREAM-AGENT provides a `workflow_call` reusable drift-guard workflow that internally runs the drift-guard composite action and publishes artifacts + PR block comment. Dreambuddy-V2 keeps a thin `drift-guard` workflow (stable check name) that calls the reusable workflow pinned to `drift-guard/v0.1.0`. Local scheduled sessions remain paused or are converted to read-only/dispatch-only.

**Tech Stack:** GitHub Actions, gh CLI, Git tags, Python 3 stdlib.

---

## File Structure (What to Create / Modify)

**DREAM-AGENT**
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/workflows/reusable-drift-guard.yml`
- Modify: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/docs/feishu-collab/runbooks/` (create new doc)
- Modify: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/docs/superpowers/specs/2026-06-09-drift-guard-cross-repo-reuse-and-automation-recovery-design.md` (optional: link to runbook)

**Dreambuddy-V2**
- Modify: `/Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.github/workflows/drift-guard.yml` (thin wrapper -> calls reusable workflow)
- Delete: `/Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.github/actions/drift-guard/` (vendored action)

---

### Task 1: Add reusable drift-guard workflow in DREAM-AGENT

**Files:**
- Create: [reusable-drift-guard.yml](file:///Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/workflows/reusable-drift-guard.yml)

- [ ] **Step 1: Create reusable workflow (workflow_call)**

```yaml
name: reusable-drift-guard

on:
  workflow_call:
    inputs:
      change_class:
        required: true
        type: string
      config_path:
        required: false
        type: string
        default: ".workbuddy/drift-guard.json"
      comment_on_pr_block:
        required: false
        type: boolean
        default: true

permissions: {}

jobs:
  guard:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          clean: true

      - name: Ensure clean workspace
        shell: bash
        run: |
          set -e
          git reset --hard
          git clean -fdx
          git fetch origin main --depth=1

      - name: Run drift guard
        id: drift
        uses: ./.github/actions/drift-guard
        with:
          mode: ${{ github.event_name == 'workflow_dispatch' && 'manual' || github.event_name }}
          change_class: ${{ inputs.change_class }}
          config_path: ${{ inputs.config_path }}
          base_sha: ${{ github.event_name == 'pull_request' && 'origin/main' || '' }}
          head_sha: ${{ github.event_name == 'pull_request' && 'HEAD' || '' }}
          report_json: drift_report.json
          report_md: drift_report.md

      - name: Upload drift report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: drift-guard-report-${{ github.run_id }}
          path: |
            drift_report.json
            drift_report.md

      - name: Comment drift report (PR block)
        if: ${{ inputs.comment_on_pr_block && failure() && github.event_name == 'pull_request' && hashFiles('drift_report.md') != '' }}
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require("fs");
            const body = fs.readFileSync("drift_report.md", "utf8");
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.payload.pull_request.number,
              body,
            });
```

- [ ] **Step 2: Commit and push (DREAM-AGENT)**

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
git checkout -b protocol/drift-guard-reuse-workflow
git add .github/workflows/reusable-drift-guard.yml
git commit -m "feat(drift-guard): add reusable drift-guard workflow"
git push -u origin protocol/drift-guard-reuse-workflow
gh pr create --repo yunya1991/DREAM-AGENT --base main --head protocol/drift-guard-reuse-workflow --title "feat(drift-guard): reusable workflow_call entrypoint" --body "Adds reusable drift-guard workflow_call so downstream repos can reuse drift-guard via pinned tags."
```

- [ ] **Step 3: Ensure checks pass and merge PR**

Verify:
- `drift-guard` passes
- `lifecycle-guard` passes (add minimal protocol comments if needed, as done previously)

Merge:

```bash
gh pr merge --repo yunya1991/DREAM-AGENT --squash --delete-branch <PR_NUMBER>
```

---

### Task 2: Tag a stable drift-guard release in DREAM-AGENT

**Goal:** Create `drift-guard/v0.1.0` tag after the reusable workflow is on main.

- [ ] **Step 1: Pull latest main and tag**

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
git checkout main
git pull --ff-only
git tag -a drift-guard/v0.1.0 -m "drift-guard reusable workflow + action v0.1.0"
git push origin drift-guard/v0.1.0
```

- [ ] **Step 2: Verify tag exists on GitHub**

Run:

```bash
gh api repos/yunya1991/DREAM-AGENT/git/ref/tags/drift-guard/v0.1.0 --jq .ref
```

Expected: `refs/tags/drift-guard/v0.1.0`

---

### Task 3: Switch Dreambuddy-V2 drift-guard to call the reusable workflow (pinned tag)

**Files:**
- Modify: [drift-guard.yml](file:///Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.github/workflows/drift-guard.yml)
- Delete: `file:///Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.github/actions/drift-guard/`

- [ ] **Step 1: Update drift-guard workflow to call reusable workflow**

Replace job body with `uses:` call while keeping stable name/job key:

```yaml
name: drift-guard

on:
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      change_class:
        required: true
        type: choice
        options: [mainline, integration, infra]
        default: mainline
  schedule:
    - cron: "10 */4 * * *"

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

permissions: {}

concurrency:
  group: drift-guard-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  guard:
    uses: yunya1991/DREAM-AGENT/.github/workflows/reusable-drift-guard.yml@drift-guard/v0.1.0
    permissions:
      contents: read
      pull-requests: write
    with:
      change_class: ${{ github.event_name == 'workflow_dispatch' && inputs.change_class || 'mainline' }}
      config_path: .workbuddy/drift-guard.json
      comment_on_pr_block: true
```

- [ ] **Step 2: Delete vendored action directory**

```bash
cd /Users/zhangjiangtao/WorkBuddy/dreambuddy-v2
rm -rf .github/actions/drift-guard
```

- [ ] **Step 3: Create PR and merge**

```bash
cd /Users/zhangjiangtao/WorkBuddy/dreambuddy-v2
git checkout -b protocol/use-dream-agent-drift-guard
git add .github/workflows/drift-guard.yml
git add -u
git commit -m "chore(drift-guard): reuse DREAM-AGENT workflow via tag"
git push -u origin protocol/use-dream-agent-drift-guard
gh pr create --repo yunya1991/Dreambuddy-V2 --base main --head protocol/use-dream-agent-drift-guard --title "chore(drift-guard): reuse DREAM-AGENT drift guard" --body "Remove vendored drift-guard action and call DREAM-AGENT reusable workflow pinned to drift-guard/v0.1.0."
```

Verify PR checks:
- `drift-guard` passes
- `lifecycle-guard` passes

Merge:

```bash
gh pr merge --repo yunya1991/Dreambuddy-V2 --squash --delete-branch <PR_NUMBER>
```

---

### Task 4: Write automation recovery policy (DREAM-AGENT)

**Files:**
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/docs/feishu-collab/runbooks/automation-recovery-policy.md`

- [ ] **Step 1: Write policy document**

Content requirements:
- Allowed local automation: read-only inspection + dispatch-only
- Permanently disabled: any local scheduled session that writes repo or pushes main
- Mapping from current paused schedules to recommended state and replacement GH workflows
- “Return to mainline flow” checklist: PR → checks → controlled-dispatch → Feishu writeback/monitoring/artifacts

- [ ] **Step 2: Commit and push**

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
git checkout -b docs/automation-recovery-policy
git add docs/feishu-collab/runbooks/automation-recovery-policy.md
git commit -m "docs(automation): add recovery policy for local schedules"
git push -u origin docs/automation-recovery-policy
gh pr create --repo yunya1991/DREAM-AGENT --base main --head docs/automation-recovery-policy --title "docs(automation): recovery policy for local schedules" --body "Defines which local schedules can be resumed and which must stay disabled now that main is protected and drift-guard exists."
```

---

### Task 5: Validation and return to mainline

- [ ] **Step 1: Create a small out-of-scope PR in Dreambuddy-V2 to validate BLOCK path**

Change an out-of-scope file (e.g. `2-GOVERNANCE/README.md`) and confirm:
- `drift-guard` fails
- PR receives `drift_report.md` comment

- [ ] **Step 2: Create a small in-scope PR (mainline) to validate PASS path**

Change under `7-产物中台/**` and confirm:
- `drift-guard` passes
- `lifecycle-guard` passes (requires minimal protocol body/comments)

- [ ] **Step 3: Use controlled-dispatch in DREAM-AGENT for the next mainline automation**

Trigger `controlled-dispatch` with an allowlisted target and verify it triggers and leaves an auditable Actions run URL.

---

## Self-Review Checklist (author)

- [ ] Plan covers: reusable workflow, tag pinning, Dreambuddy-V2 de-vendor, automation policy doc, validation
- [ ] No placeholder steps; every file path and command is concrete
- [ ] Branch names use allowed prefixes (`protocol/`, `design/`, `milestone/`, etc.) to satisfy lifecycle-guard

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-09-drift-guard-cross-repo-reuse-and-automation-recovery-implementation.md`.

Two execution options:
1) **Subagent-Driven (recommended)** — dispatch a fresh subagent per task and review between tasks
2) **Inline Execution** — execute tasks in this session with checkpoints

Which approach?


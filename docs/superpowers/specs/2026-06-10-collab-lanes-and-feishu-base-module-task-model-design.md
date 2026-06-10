# Collab Lanes And Feishu Base Module Task Model Design

> Date: 2026-06-10  
> Scope: Dreambuddy-V2 + DREAM-AGENT + Feishu Base (Dream多维表格)  
> Status: Draft  

## 1. Goal

Make “any agent can start working and plug into the collaboration system” practical by:

- Splitting collaboration into two lanes:
  - **Strict Lane** for module-level capability chain delivery.
  - **Fast Lane** for single-PR quick iteration.
- Making Feishu Base the source of truth for “module → paths → docs → OKR alignment”, so governance is driven by data rather than hand-written PR rituals.
- Keeping the core actions, but removing default friction for single-PR work.
- Removing legacy scheduled automation that no longer matches the current mainline.

## 2. Current Findings

### 2.1 Why Agent Lifecycle Guard keeps failing

The current lifecycle checker is correct but overly strict as a default:

- It expects a full set of structured comments and PR fields (Task Card, STARTED, DESIGN_REVIEW, TEST_REPORT, non-owner review, DONE, shared files declaration, branch policy).
- For new agents or single PR pushes, missing any of those yields BLOCK, even when code and tests are real.

### 2.2 Feishu Base already has 3 layers, but the “module task layer” is missing

In “Dream多维表格”, there are three tables:

- `目标推进表` — goal / OKR alignment overview (already rich).
- `自动化任务监控` — workflow / PR / run monitoring (already rich).
- `数据表` — currently too thin (only task title + Objective/KR ids), not enough for module-level decomposition.

### 2.3 Dreambuddy-V2 already has a coarse drift guard module, but not a fine module map

`dreambuddy-v2/.workbuddy/drift-guard.json` already allows `product_hub` as the mainline module for `7-产物中台/**`, but it is not the same thing as “feature modules”.

We need an additional “module task model” to drive lane selection and lifecycle expectations, while drift-guard continues to provide repo scope protection.

## 3. Design Overview

### 3.1 Three-table model (Base as source of truth)

We standardize the collaboration data model as:

1. **Goal layer**: `目标推进表` (existing)
2. **Module task layer**: rename/upgrade `数据表` into a real **模块任务表** (new/upgrade)
3. **Run layer**: `自动化任务监控` (existing)

### 3.1.1 Preflight gate (Doc → Approval/DESIGN_REVIEW → OKR → Base)

Before any “real work” starts (including Fast Lane), we require a hard preflight gate:

- **First kickoff (project/module)**: requires BOTH
  - Feishu approval instance
  - DESIGN_REVIEW record (doc link)
  - Owner must confirm approval + review completed
- **Every run / every automation execution**:
  - Spec + Plan are present and approved
  - Feishu OKR Objective exists (Objective link/id)
  - Base `目标推进表` has a goal bound to the Objective (`goal_id`)
  - Base `模块任务表` has a task record (`task_id`) bound to `goal_id`, with `lane_type/module_paths/spec_doc/plan_doc` complete

If anything is missing, the executor must **fill the missing Feishu OKR / Base records first**. No STARTED/SUMMARY/DONE is allowed until the gate is satisfied.

### 3.2 Two collaboration lanes

- **Strict Lane (module)**: keep full core actions and strict governance.
- **Fast Lane (single PR)**: keep only the minimal core actions; allow agents to move quickly.

## 4. Module Task Layer (Feishu Base)

### 4.1 Table rename

Rename:

- `数据表` -> `模块任务表`

### 4.2 Required fields (module task record)

Add/ensure the following fields exist in `模块任务表`:

- `task_id` (text, primary key recommended)
- `task_title` (text)
- `goal_id` (text, links to `目标推进表.goal_id`)
- `okr_objective_id` (text)
- `kr_id` (text)
- `module_key` (select)
- `module_paths` (text; newline-separated glob paths, repo-relative)
- `lane_type` (select: `strict` / `fast`)
- `spec_doc` (text; repo path or URL)
- `plan_doc` (text; repo path or URL)
- `repo` (text; default `yunya1991/Dreambuddy-V2`)
- `branch_prefix` (select: `milestone` / `agent` / `pilot` / `acceptance`)
- `status` (select: `backlog` / `in_progress` / `blocked` / `done`)
- `pr_number` (text)
- `pr_url` (text)
- `comment_anchor` (text)
- `blocker` (text)
- `next_action` (text)

### 4.3 Initial module map (v0)

The first module map must strictly reference existing approved docs:

- **ui-map real data integration**
  - Spec: `7-产物中台/docs/superpowers/specs/2026-06-07-ui-map-real-data-integration-contract.md`
  - Plan: `7-产物中台/docs/superpowers/plans/2026-05-22-ui-map-independent-hub-main-map-implementation.md`
  - Paths:
    - `7-产物中台/系统研究索引体系/app/ui-map/*`
    - `7-产物中台/系统研究索引体系/lib/*` (only when explicitly needed by the contract)
- **product hub directory migration**
  - Spec: `7-产物中台/docs/superpowers/specs/2026-05-22-product-hub-directory-migration-design.md`
  - Plan: `7-产物中台/docs/superpowers/plans/2026-05-22-product-hub-directory-migration-implementation.md`
  - Paths:
    - `7-产物中台/*` (but keep the task scope as narrow as the current step in the plan)

The module map is expected to expand, but every new module must come from a spec/plan first.

## 5. Lane Rules

### 5.1 How lane is determined

Lane is determined by `模块任务表.lane_type`, and must be mirrored into the PR body for GitHub-side evaluation:

- If a PR references a module task record whose `lane_type=strict`, then Strict Lane applies.
- Otherwise, Fast Lane applies.

### 5.2 Strict Lane core actions (kept as-is)

Strict Lane requires:

- Task Card present (PR body references `task_id` and `goal_id`)
- `[协作开工声明 / STARTED]`
- `[方案评审记录 / DESIGN_REVIEW]`
- `[测试报告 / TEST_REPORT]`
- Non-owner review present
- `[协作完成回报 / DONE]`

### 5.3 Fast Lane core actions (reduced, but still traceable)

Fast Lane requires:

- Preflight gate satisfied (Doc → Approval/DESIGN_REVIEW → OKR → Base)
- Task Card present (PR body references `task_id` + `goal_id`)
- One single summary comment including:
  - what changed
  - how verified (test command + result)
  - current status / next step

Fast Lane does not require non-owner review by default.

## 6. GitHub Protocol Surface

### 6.1 PR body minimal fields

Update Dreambuddy-V2 PR template to include:

- `Task ID` (module task id in Base)
- `Goal ID` (optional for Fast; required for Strict)
- `Lane` (`strict` / `fast`)
- `Module Key`
- `Module Paths` (newline list)
- `Spec Doc`
- `Plan Doc`

This keeps GitHub-side checks deterministic without requiring GitHub Actions to read Feishu.

### 6.2 Agent comment templates

- Keep existing structured comment headers for Strict Lane.
- For Fast Lane, allow a single summary comment without forcing the full structured protocol.

## 7. Lifecycle Guard Changes (Design)

### 7.1 Make it lane-aware

Modify the lifecycle payload builder/checker to:

- Detect lane from PR body (`Lane: fast|strict`).
- Apply a different required rule set per lane:
  - Strict: current full rules.
  - Fast: reduced rules.

### 7.2 Keep strictness for module work, reduce friction for single PR

This preserves governance where it matters, while restoring throughput for incremental PRs.

## 8. Legacy Automation Cleanup (Design)

Disable or remove legacy scheduled automation that is no longer part of the current mainline:

- GitHub workflows: `pr9-*` scheduled chains should be disabled (keep manual dispatch only if explicitly needed).
- Local scheduled tasks: `PR9 Developer/Validator/Governance` and unrelated dreambuddy-v1 protocol tasks should be removed or kept paused.

## 9. Acceptance Criteria

- A new agent can create a Fast Lane PR and pass lifecycle guard using only the minimal required fields + a summary comment.
- A module task marked Strict Lane continues to enforce the full protocol and non-owner review.
- Base has an explicit module task layer: module_key + module_paths + spec/plan anchors + okr alignment.
- Legacy pr9 scheduled noise is removed, leaving only current mainline workflows.

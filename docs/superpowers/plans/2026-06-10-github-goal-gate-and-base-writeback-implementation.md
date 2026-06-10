# GitHub Goal Gate And Base Writeback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Fast lane require `Goal ID` plus mandatory preflight/post-update fields, and make the automation executor project those fields and write back task/goal/monitor records to Feishu Base.

**Architecture:** Split the work into two independent but connected tracks. `dreambuddy-v2` owns GitHub-side protocol parsing, PR template shape, and lifecycle blocking rules. `DREAM-AGENT` owns Feishu-side projection and writeback execution for task/goal/monitor tables. Both tracks are implemented test-first so the protocol becomes executable rather than doc-only.

**Tech Stack:** Python 3, GitHub Actions payload scripts, JSON rule registry, unittest, Feishu Base via `lark-cli`

---

### Task 1: Tighten GitHub Lifecycle Payload In `dreambuddy-v2`

**Files:**
- Modify: `dreambuddy-v2/AGENT协作工具/github-actions/build_agent_lifecycle_payload.py`
- Modify: `dreambuddy-v2/AGENT协作工具/github-actions/check_agent_lifecycle.py`
- Modify: `dreambuddy-v2/AGENT协作工具/SKILLS/agent-collab-supervisor/rules.json`
- Modify: `dreambuddy-v2/.github/pull_request_template.md`
- Create: `dreambuddy-v2/tests/test_agent_lifecycle_goal_gate.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Verify Fast lane without `Goal ID` is blocked**
- [ ] **Step 3: Verify STARTED/SUMMARY missing preflight/post-update fields is blocked**
- [ ] **Step 4: Implement payload parsing for `Lane` / `Goal ID` / preflight / post-update markers**
- [ ] **Step 5: Implement lane-aware checker rules for Fast lane**
- [ ] **Step 6: Update PR template to expose the required fields**
- [ ] **Step 7: Run lifecycle tests**

### Task 2: Project Protocol Fields Into Feishu Writeback In `DREAM-AGENT`

**Files:**
- Modify: `DREAM-AGENT/github-actions/sync_github_to_feishu.py`
- Modify: `DREAM-AGENT/github-actions/build_goal_progress_record.py`
- Modify: `DREAM-AGENT/github-actions/feishu_collab/github_sync/build_github_sync_preview.py`
- Modify: `DREAM-AGENT/github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py`
- Create: `DREAM-AGENT/github-actions/tests/test_github_sync_protocol_writeback.py`

- [ ] **Step 1: Write failing tests for preflight/post-update projection**
- [ ] **Step 2: Extend task record projection with protocol check fields and Base writeback payload**
- [ ] **Step 3: Extend goal projection with sync/writeback summary fields**
- [ ] **Step 4: Extend github sync preview/materialization so run execution carries task/goal/monitor writeback payloads**
- [ ] **Step 5: Run focused `DREAM-AGENT` tests**

### Task 3: Enforce Three-Table Writeback In The Automation Executor

**Files:**
- Modify: `DREAM-AGENT/github-actions/poll_feishu_approval_and_sync_base.py`
- Modify: `DREAM-AGENT/github-actions/run_approval_polling_writeback.py`
- Modify: `DREAM-AGENT/github-actions/tests/test_poll_feishu_approval_and_sync_base.py`

- [ ] **Step 1: Write failing tests proving task/goal/monitor writeback all happen**
- [ ] **Step 2: Extend writeback input contract with monitor table sync config**
- [ ] **Step 3: Implement third-table upsert and partial-failure receipts**
- [ ] **Step 4: Run focused writeback tests**

### Task 4: Verify End-To-End Behavior

**Files:**
- Reuse tests from Task 1-3

- [ ] **Step 1: Run `dreambuddy-v2` lifecycle test suite for the new rules**
- [ ] **Step 2: Run `DREAM-AGENT` github sync + writeback tests**
- [ ] **Step 3: Summarize exact protocol fields now required by GitHub and exact Base fields now written by the executor**

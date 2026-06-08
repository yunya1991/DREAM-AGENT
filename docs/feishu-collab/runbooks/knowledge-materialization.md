# Knowledge Materialization

## Purpose

Consume approval and polling artifacts, write one governed runbook and one governed handoff document, and update the knowledge indexes.

## Workflow Entry

- Workflow: `.github/workflows/knowledge-materialization.yml`
- Trigger: `workflow_dispatch`
- Required inputs:
  - `approval_status_result_json`
  - `approval_writeback_result_json`
  - `materialization_context_json`

## Artifacts

- `knowledge_materialization_result.json`

## Success Rule

The workflow succeeds only when both the runbook and handoff are written and both indexes are updated.

## Failure Guide

- If runbook write fails, inspect the materialization result before rerunning.
- If handoff write fails, keep the runbook and rerun after fixing the handoff path.
- If index update fails, keep the documents and repair the indexes before the next run.

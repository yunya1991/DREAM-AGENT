# Five Skill Integration Rehearsal

## Purpose

Run the fixture-driven system rehearsal for:

1. `OKR-driven`
2. `Bitable`
3. `GitHub Sync`
4. `Approval`
5. `Knowledge-Ops`

This runbook verifies that the core objective baseline can move through the full collaboration chain with one normalized system result.

## Local Command

    python3 github-actions/run_five_skill_integration_rehearsal.py

## Workflow Entry

- Workflow: `.github/workflows/five-skill-rehearsal.yml`
- Trigger: `workflow_dispatch`
- Artifact report: `five-skill-rehearsal-report.json`
- Primary GitHub surface: `Job Summary`

## Expected Output

- `scenario_manifest`
- `step_results`
- `breakpoints`
- `system_status`
- `verification_summary`
- `handoff`
- `knowledge_update`

## Status Reading Guide

- `pass`: the step completed without a system breakpoint
- `warn`: the workflow renders evidence but exits failed for operator review
- `fail`: the workflow renders evidence and exits failed because a contract or execution issue remains
- `blocked`: the workflow renders evidence and exits failed because the chain cannot continue safely

## Recovery Guide

- If `policy_gap`, fix the governance input and rerun
- If `data_gap`, repair the fixture or missing reference and rerun
- If `contract_gap`, align the step interface and rerun
- If `execution_gap`, inspect the skill output and rerun

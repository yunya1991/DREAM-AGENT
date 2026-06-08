# Five Skill Integration Rehearsal

## Purpose

Run the fixture-driven system rehearsal for:

1. `OKR-driven`
2. `Bitable`
3. `GitHub Sync`
4. `Approval`
5. `Knowledge-Ops`

This runbook verifies that the core objective baseline can move through the full collaboration chain with one normalized system result.

## Command

    python3 github-actions/run_five_skill_integration_rehearsal.py

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
- `warn`: the step completed with degraded evidence and the chain continued
- `fail`: the step completed with a non-blocking contract or execution issue
- `blocked`: the step cannot safely continue and the chain stops

## Recovery Guide

- If `policy_gap`, fix the governance input and rerun
- If `data_gap`, repair the fixture or missing reference and rerun
- If `contract_gap`, align the step interface and rerun
- If `execution_gap`, inspect the skill output and rerun

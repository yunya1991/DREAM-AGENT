---
name: "feishu-collab-knowledge-ops"
description: "Normalizes KnowledgeUpdate intake, validates governed asset targets, checks drift/gap/stale signals, writes governed knowledge assets, and emits handoff after verification."
---

# Feishu Collaboration Knowledge Ops

## When to use

Use this skill when:

- another Feishu collaboration skill emits a `KnowledgeUpdate`
- a handoff or runbook needs governed routing and validation
- the user needs drift/gap/stale checks before storing knowledge
- the flow must emit verification and governance handoff after writeback

## Inputs

- `KnowledgeUpdate`
- optional handoff summary and source skill metadata
- optional existing asset/index state

## Flow

1. normalize knowledge intake
2. build preview with target, validation, and checks
3. confirm writeback or overwrite
4. materialize governed asset
5. verify file and index alignment
6. generate handoff and `KnowledgeUpdate` receipt

## Guardrails

- never skip preview
- treat unknown asset type as hard block
- treat empty title as hard block
- treat missing evidence or index gaps as soft block
- treat stale assets as degraded success
- do not expand into dashboards in v1

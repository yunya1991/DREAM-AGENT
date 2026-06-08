---
name: "feishu-collab-bitable"
description: "Projects OKR-driven outputs into Base task, progress, and view-validation previews, then writes back after confirmation. Invoke when aligning long-term goal structure with short-term execution records in Feishu Base."
---

# Feishu Collaboration Bitable

## When to use

Use this skill when:

- `OKR-driven` already produced a goal/task preview
- the user needs Base task and progress projection
- the user needs boss-view or execution-view validation
- the user wants preview-before-writeback

## Inputs

- upstream `ExecutionPreview`
- current Base context
- optional existing task/progress records

## Flow

1. build preview
2. review drift flags
3. confirm execution
4. write back tasks/progress/projection
5. verify output
6. generate handoff and `KnowledgeUpdate`

## Guardrails

- never redefine the goal outside upstream input
- never skip preview
- treat missing required fields as hard block
- treat missing view validation as degraded success

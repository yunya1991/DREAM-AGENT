---
name: "feishu-collab-approval"
description: "Evaluates high-risk actions, creates or reuses Feishu approval instances, polls decision status, and writes the result back into collaboration state after confirmation."
---

# Feishu Collaboration Approval

## When to use

Use this skill when:

- a high-risk action needs governance review before execution continues
- the user needs approval preview-before-create
- the workflow must create or reuse a Feishu approval instance
- the flow must poll decision status and project it back into collaboration records

## Inputs

- risk context
- approval config
- optional existing approval instance code
- optional sibling task / goal context

## Flow

1. evaluate risk gate
2. build preview
3. confirm approval creation or reuse
4. create or poll approval instance
5. project status and automation outcome
6. generate handoff and `KnowledgeUpdate`

## Guardrails

- never skip preview
- treat missing approval code as hard block
- treat missing applicant open_id as hard block
- treat polling failures as soft block
- treat missing evidence snapshot as degraded success
- do not expand into approval dashboards in v1

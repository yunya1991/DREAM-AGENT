---
name: "feishu-collab-github-sync"
description: "Projects GitHub issue, PR, and checks events into Feishu collaboration state, then writes back after confirmation with verification and handoff."
---

# Feishu Collaboration GitHub Sync

## When to use

Use this skill when:

- the user needs GitHub issue, PR, or checks status reflected in Feishu collaboration records
- a workflow or event hook has already produced GitHub event payloads
- the user needs preview-before-writeback for engineering collaboration updates
- the flow must emit verification notes, handoff, and `KnowledgeUpdate`

## Inputs

- normalized or raw GitHub event payload
- current Feishu collaboration context
- optional approval context

## Flow

1. build preview
2. review coverage hit and risk flags
3. confirm execution or trigger policy check
4. write back collaboration state
5. verify fields, automation summary, and comment anchor
6. generate handoff and `KnowledgeUpdate`

## Guardrails

- never skip preview
- treat missing task lookup as hard block
- treat event coverage gaps as soft block
- treat missing comment anchor as degraded success
- do not default to remote GitHub mutations in v1
